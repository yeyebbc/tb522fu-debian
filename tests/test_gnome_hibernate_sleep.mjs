// SPDX-License-Identifier: GPL-2.0-only
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source = fs.readFileSync(new URL('../device/gnome-hibernate-sleep/extension.js', import.meta.url), 'utf8');

async function fixture({board = 'lenovo-tb522fu', accepted = true} = {}) {
    const f = {accepted, calls: [], errors: 0, signals: new Map()};
    const Main = {sessionMode: {isLocked: false, isGreeter: false}, notifyError() {f.errors++;}};
    const actions = {
        _actions: new Map([['suspend', {available: false}]]), canLockScreen: true,
        get canSuspend() {return this._actions.get('suspend').available;},
        _updateSuspend() {this._actions.get('suspend').available = false;},
        activateSuspend() {throw Error('Original RAM suspend must never run');},
        connect(name, callback) {const id=f.signals.size+1; f.signals.set(id,[name,callback]); return id;},
        disconnect(id) {f.signals.delete(id);}, notify() {},
    };
    const original = actions.activateSuspend;
    const Gio = {
        File: {new_for_path(path) {return {
            load_contents() {assert.equal(path,'/etc/tb522fu/board'); return [true,Buffer.from(board)];},
            query_exists() {assert.equal(path,'/etc/tb522fu/hibernate-accepted'); return f.accepted;},
        };}},
        DBusCallFlags: {NONE: 0},
        DBus: {system: {
            call(...args) {
                f.calls.push(args.slice(0,9));
                queueMicrotask(() => args[9](this,null));
            },
            call_finish() {if(f.fail) throw Error('logind rejected hibernation');},
        }},
    };
    class InjectionManager {
        constructor(){this.undo=[];}
        overrideMethod(object,name,create){const old=object[name];this.undo.push(()=>object[name]=old);object[name]=create(old);}
        clear(){for(const undo of this.undo.reverse())undo();this.undo=[];}
    }
    const GLib = {Variant: class {constructor(type,value){this.type=type;this.value=value;}}};
    const context = vm.createContext({TextDecoder,console:{log(){},error(){}}});
    const imports = new Map([
        ['gi://Gio',{default:Gio}],['gi://GLib',{default:GLib}],
        ['resource:///org/gnome/shell/extensions/extension.js',{Extension:class {},InjectionManager}],
        ['resource:///org/gnome/shell/ui/main.js',Main],
        ['resource:///org/gnome/shell/misc/systemActions.js',{getDefault:()=>actions}],
    ]);
    const module = new vm.SourceTextModule(source,{context});
    await module.link(async name=>{const values=imports.get(name);assert.ok(values);return new vm.SyntheticModule(Object.keys(values),function(){for(const [key,value]of Object.entries(values))this.setExport(key,value);},{context});});
    await module.evaluate();
    Object.assign(f,{extension:new module.namespace.default(),actions,Main,original});
    return f;
}
let count=0;
async function test(name,run){await run();count++;console.log('PASS '+name);}
const settle=()=>new Promise(resolve=>setImmediate(resolve));

await test('Suspend uses normal logind Hibernate and authorization',async()=>{
    const f=await fixture();f.extension.enable();f.actions.activateSuspend();await settle();
    assert.equal(f.calls.length,1);
    const args=f.calls[0];
    assert.deepEqual(args.slice(0,4),['org.freedesktop.login1','/org/freedesktop/login1','org.freedesktop.login1.Manager','Hibernate']);
    assert.equal(args[4].type,'(b)');assert.deepEqual(Array.from(args[4].value),[true]);
    assert.equal(args[8],null);f.extension.disable();
});
await test('unaccepted or foreign devices cannot replace the original action',async()=>{
    for(const options of [{accepted:false},{board:'other'}]){
        const f=await fixture(options);assert.throws(()=>f.extension.enable());
        assert.equal(f.actions.activateSuspend,f.original);assert.equal(f.calls.length,0);
    }
});
await test('locked, greeter and no-lock sessions cannot request hibernation',async()=>{
    const f=await fixture();f.extension.enable();
    for(const key of ['isLocked','isGreeter']){f.Main.sessionMode[key]=true;f.actions._updateSuspend();f.actions.activateSuspend();f.Main.sessionMode[key]=false;}
    f.actions.canLockScreen=false;f.actions._updateSuspend();f.actions.activateSuspend();await settle();
    assert.equal(f.calls.length,0);f.extension.disable();
});
await test('revoked acceptance and logind failure never fall back to RAM suspend',async()=>{
    const f=await fixture();f.extension.enable();f.accepted=false;f.actions.activateSuspend();await settle();
    assert.equal(f.calls.length,0);assert.equal(f.errors,1);
    f.accepted=true;f.fail=true;f.actions.activateSuspend();await settle();
    assert.equal(f.calls.length,1);assert.equal(f.errors,2);f.extension.disable();
});
await test('duplicate activation coalesces and disable restores the original action',async()=>{
    const f=await fixture();f.extension.enable();f.actions.activateSuspend();f.actions.activateSuspend();
    // Lock mode disables extensions while logind's accepted sleep request runs.
    f.extension.disable();await settle();assert.equal(f.calls.length,1);
    assert.equal(f.actions.activateSuspend,f.original);assert.equal(f.signals.size,0);
});
console.log(`${count} hibernation Suspend checks passed`);
