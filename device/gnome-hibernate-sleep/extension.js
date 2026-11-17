// SPDX-License-Identifier: GPL-2.0-only
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import {Extension, InjectionManager} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as SystemActions from 'resource:///org/gnome/shell/misc/systemActions.js';

export default class HibernateSleep extends Extension {
    enable() {
        const [, board] = Gio.File.new_for_path('/etc/tb522fu/board').load_contents(null);
        if (new TextDecoder().decode(board).trim() !== 'lenovo-tb522fu')
            throw new Error('Hibernation action is limited to Lenovo TB522FU');
        if (!Gio.File.new_for_path('/etc/tb522fu/hibernate-accepted').query_exists(null))
            throw new Error('Complete native hibernation acceptance before enabling the menu action');
        this._actions = SystemActions.getDefault();
        this._injections = new InjectionManager();
        const extension = this;
        this._injections.overrideMethod(this._actions, '_updateSuspend', () => function () {
            this._actions.get('suspend').available = this.canLockScreen &&
                !Main.sessionMode.isLocked && !Main.sessionMode.isGreeter;
            this.notify('can-suspend');
        });
        this._injections.overrideMethod(this._actions, 'activateSuspend', () => function () {
            extension._activate().catch(error => {
                console.error(`Hibernation Suspend: ${error.message}`);
                Main.notifyError('Hibernation could not start', error.message);
            });
        });
        this._lockSignal = this._actions.connect('notify::can-lock-screen',
            () => this._actions._updateSuspend());
        this._actions._updateSuspend();
    }

    async _activate() {
        if (this._pending || !this._actions?.canLockScreen ||
            !this._actions.canSuspend || Main.sessionMode.isLocked || Main.sessionMode.isGreeter)
            return;
        this._pending = true;
        try {
            if (!Gio.File.new_for_path('/etc/tb522fu/hibernate-accepted').query_exists(null))
                throw new Error('Hibernation acceptance was removed');
            // Use logind's normal authorization and PrepareForSleep/inhibitor
            // protocol. GNOME locks through that protocol before the snapshot.
            // This request is not cancelled when Shell enters its locked mode.
            console.log('Hibernation Suspend: requesting logind Hibernate');
            await new Promise((resolve, reject) => {
                Gio.DBus.system.call('org.freedesktop.login1', '/org/freedesktop/login1',
                    'org.freedesktop.login1.Manager', 'Hibernate',
                    new GLib.Variant('(b)', [true]), null, Gio.DBusCallFlags.NONE,
                    30000, null, (connection, result) => {
                        try { connection.call_finish(result); resolve(); }
                        catch (error) { reject(error); }
                    });
            });
        } finally {
            this._pending = false;
        }
    }

    disable() {
        if (this._lockSignal)
            this._actions.disconnect(this._lockSignal);
        this._lockSignal = null;
        this._injections?.clear();
        this._injections = null;
        this._actions?._updateSuspend();
        this._actions = null;
    }
}
