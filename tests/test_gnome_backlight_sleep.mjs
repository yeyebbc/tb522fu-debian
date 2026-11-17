// SPDX-License-Identifier: GPL-2.0-only
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../device/gnome-backlight-sleep/extension.js', import.meta.url), 'utf8');
const compat = 'mode=compat\nmdss_power_control=on\ngsd_power=123:1000:adapter\n';

async function fixture({board = 'lenovo-tb522fu', masks = true, status = compat} = {}) {
    const f = {status, modeCalls: 0, locks: 0, kernelSleeps: 0, errors: 0, signals: new Map(), sources: new Map()};
    const Main = {sessionMode: {isLocked: false, isGreeter: false}, notifyError() { f.errors++; }};
    const actions = {
        _actions: new Map([['suspend', {available: false}]]),
        canLockScreen: true,
        get canSuspend() { return this._actions.get('suspend').available; },
        _updateSuspend() { this._actions.get('suspend').available = false; },
        activateSuspend() { f.kernelSleeps++; },
        activateLockScreen() { f.locks++; },
        connect(name, callback) { const id = f.signals.size + 1; f.signals.set(id, [name, callback]); return id; },
        disconnect(id) { f.signals.delete(id); },
        notify() {},
    };
    const originalActivate = actions.activateSuspend;
    const originalUpdate = actions._updateSuspend;
    const Gio = {
        FileQueryInfoFlags: {NOFOLLOW_SYMLINKS: 1},
        IOErrorEnum: {CANCELLED: 19},
        SubprocessFlags: {STDOUT_PIPE: 1, STDERR_PIPE: 2},
        Cancellable: class { cancel() {} },
        File: {new_for_path(path) {
            return {
                load_contents() { assert.equal(path, '/etc/tb522fu/board'); return [true, Buffer.from(board)]; },
                query_info() { return {get_is_symlink: () => masks, get_symlink_target: () => '/dev/null'}; },
            };
        }},
        Subprocess: {new(args) {
            assert.deepEqual(Array.from(args), ['/usr/sbin/tb522fu-display-power-mode', 'status']);
            f.modeCalls++;
            return {
                communicate_utf8_async(_input, _cancel, callback) {
                    queueMicrotask(() => { f.beforeReply?.(); callback(this, null); });
                },
                communicate_utf8_finish() { return [true, f.status, '']; },
                get_successful() { return true; },
                force_exit() {},
            };
        }},
    };
    let nextSource = 1;
    const GLib = {
        PRIORITY_DEFAULT: 0, SOURCE_REMOVE: false,
        timeout_add(_priority, _time, callback) { const id = nextSource++; f.sources.set(id, callback); return id; },
        Source: {remove(id) { f.sources.delete(id); }},
    };
    class InjectionManager {
        constructor() { this.restore = []; }
        overrideMethod(object, name, create) {
            const original = object[name];
            this.restore.push(() => { object[name] = original; });
            object[name] = create(original);
        }
        clear() { for (const restore of this.restore.reverse()) restore(); this.restore = []; }
    }
    const context = vm.createContext({TextDecoder, console: {log() {}, error() {}}});
    const modules = new Map([
        ['gi://Gio', {default: Gio}],
        ['gi://GLib', {default: GLib}],
        ['resource:///org/gnome/shell/extensions/extension.js', {Extension: class {}, InjectionManager}],
        ['resource:///org/gnome/shell/ui/main.js', Main],
        ['resource:///org/gnome/shell/misc/systemActions.js', {getDefault: () => actions}],
    ]);
    const module = new vm.SourceTextModule(source, {context});
    await module.link(async name => {
        const values = modules.get(name); assert.ok(values, name);
        return new vm.SyntheticModule(Object.keys(values), function () {
            for (const [key, value] of Object.entries(values)) this.setExport(key, value);
        }, {context});
    });
    await module.evaluate();
    f.extension = new module.namespace.default();
    Object.assign(f, {actions, Main, originalActivate, originalUpdate});
    return f;
}

let count = 0;
async function test(name, run) { await run(); count++; console.log(`PASS ${name}`); }
const settle = () => new Promise(resolve => setImmediate(resolve));

await test('real Suspend disabled: menu redirects through ordinary GNOME password lock', async () => {
    const f = await fixture(); await f.extension.enable();
    assert.equal(f.actions.canSuspend, true);
    f.actions.activateSuspend(); await settle();
    assert.equal(f.locks, 1); assert.equal(f.kernelSleeps, 0);
    assert.equal(f.modeCalls, 1); assert.equal(f.sources.size, 0);
    f.extension.disable();
});
await test('disable restores original action and capability without changing real sleep policy', async () => {
    const f = await fixture(); await f.extension.enable(); f.extension.disable();
    assert.equal(f.actions.activateSuspend, f.originalActivate);
    assert.equal(f.actions._updateSuspend, f.originalUpdate);
    assert.equal(f.actions.canSuspend, false); assert.equal(f.signals.size, 0); assert.equal(f.sources.size, 0);
});
await test('foreign board refuses enable before any action injection', async () => {
    const f = await fixture({board: 'different-tablet'});
    await assert.rejects(() => f.extension.enable());
    assert.equal(f.actions.activateSuspend, f.originalActivate); assert.equal(f.kernelSleeps, 0);
});
await test('missing real-sleep masks refuse enable', async () => {
    const f = await fixture({masks: false}); await assert.rejects(() => f.extension.enable());
    assert.equal(f.actions.activateSuspend, f.originalActivate);
});
await test('mode changed after enable fails without unlocked blank or fallback suspend', async () => {
    const f = await fixture(); await f.extension.enable(); f.status = 'mode=standard\n';
    f.actions.activateSuspend(); await settle();
    assert.equal(f.locks, 0); assert.equal(f.kernelSleeps, 0); assert.equal(f.errors, 1);
    f.extension.disable();
});
await test('startup may precede gsd-power; missing running adapter rejects the action', async () => {
    const f = await fixture({status: 'mode=compat\nmdss_power_control=on\ngsd_power=123:1000:no-adapter\n'});
    await f.extension.enable(); assert.equal(f.modeCalls, 0);
    f.actions.activateSuspend(); await settle();
    assert.equal(f.locks, 0); assert.equal(f.kernelSleeps, 0); assert.equal(f.errors, 1);
    f.extension.disable();
});
await test('greeter and locked sessions do not advertise Suspend', async () => {
    const f = await fixture(); await f.extension.enable();
    for (const key of ['isLocked', 'isGreeter']) {
        f.Main.sessionMode[key] = true; f.actions._updateSuspend();
        assert.equal(f.actions.canSuspend, false); f.actions.activateSuspend(); await settle();
        f.Main.sessionMode[key] = false;
    }
    assert.equal(f.locks, 0); assert.equal(f.kernelSleeps, 0); f.extension.disable();
});
await test('lock policy revoked while mode query runs prevents any blanking', async () => {
    const f = await fixture(); await f.extension.enable();
    f.beforeReply = () => { f.actions.canLockScreen = false; };
    f.actions.activateSuspend(); await settle(); assert.equal(f.locks, 0); assert.equal(f.kernelSleeps, 0);
    f.extension.disable();
});
await test('duplicate activation coalesces into one lock action', async () => {
    const f = await fixture(); await f.extension.enable();
    f.actions.activateSuspend(); f.actions.activateSuspend(); await settle();
    assert.equal(f.locks, 1); assert.equal(f.modeCalls, 1); assert.equal(f.kernelSleeps, 0);
    f.extension.disable();
});
console.log(`${count} backlight-only Suspend checks passed`);
