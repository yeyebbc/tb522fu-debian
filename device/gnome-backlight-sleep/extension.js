// SPDX-License-Identifier: GPL-2.0-only
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import {Extension, InjectionManager} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as SystemActions from 'resource:///org/gnome/shell/misc/systemActions.js';

export default class BacklightSleep extends Extension {
    async enable() {
        this._injections = new InjectionManager();
        this._cancellable = new Gio.Cancellable();
        this._processes = new Set();
        this._timeouts = new Set();
        try {
            const [, contents] = Gio.File.new_for_path('/etc/tb522fu/board').load_contents(null);
            if (new TextDecoder().decode(contents).trim() !== 'lenovo-tb522fu')
                throw new Error('Backlight-only Suspend is limited to the Lenovo TB522FU');
            // Shell extensions can start before gsd-power. Check the static
            // protection now and the running adapter when an action is used.
            this._checkProtection();
            this._actions = SystemActions.getDefault();
            const extension = this;
            this._injections.overrideMethod(this._actions, '_updateSuspend', () => function () {
                // Availability follows the ordinary password-lock policy. The
                // real logind suspend capability stays disabled by its masks.
                this._actions.get('suspend').available = this.canLockScreen &&
                    !Main.sessionMode.isLocked && !Main.sessionMode.isGreeter;
                this.notify('can-suspend');
            });
            this._injections.overrideMethod(this._actions, 'activateSuspend', () => function () {
                extension._activate().catch(error => {
                    if (!error.matches?.(Gio.IOErrorEnum, Gio.IOErrorEnum.CANCELLED)) {
                        console.error(`Backlight-only Suspend: ${error.message}`);
                        Main.notifyError('Screen-only sleep is unavailable',
                            'Display compatibility mode and screen locking must be enabled.');
                    }
                });
            });
            this._lockSignal = this._actions.connect('notify::can-lock-screen',
                () => this._actions._updateSuspend());
            this._actions._updateSuspend();
            console.log('Backlight-only Suspend: enabled; kernel sleep remains blocked');
        } catch (error) {
            this.disable();
            throw error;
        }
    }

    _checkProtection() {
        for (const unit of ['sleep.target', 'suspend.target']) {
            const info = Gio.File.new_for_path(`/etc/systemd/system/${unit}`).query_info(
                'standard::is-symlink,standard::symlink-target',
                Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS, null);
            if (!info.get_is_symlink() || info.get_symlink_target() !== '/dev/null')
                throw new Error('The real system-sleep protection is unavailable');
        }
    }

    async _checkCompat() {
        this._checkProtection();
        const process = Gio.Subprocess.new(['/usr/sbin/tb522fu-display-power-mode', 'status'],
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE);
        const processes = this._processes;
        const timeouts = this._timeouts;
        processes.add(process);
        const timeout = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 5000, () => {
            timeouts.delete(timeout);
            process.force_exit();
            return GLib.SOURCE_REMOVE;
        });
        timeouts.add(timeout);
        try {
            const output = await new Promise((resolve, reject) => {
                process.communicate_utf8_async(null, this._cancellable, (proc, result) => {
                    try {
                        const [, stdout] = proc.communicate_utf8_finish(result);
                        if (!proc.get_successful())
                            throw new Error('Display compatibility status is unavailable');
                        resolve(stdout);
                    } catch (error) {
                        reject(error);
                    }
                });
            });
            if (!/^mode=compat$/m.test(output) ||
                !/^mdss_power_control=on$/m.test(output) ||
                !/^gsd_power=\d+:\d+:adapter$/m.test(output))
                throw new Error('The running GNOME power daemon is not in backlight mode');
        } finally {
            processes.delete(process);
            if (timeouts.delete(timeout))
                GLib.Source.remove(timeout);
        }
    }

    async _activate() {
        if (this._pending || !this._actions?.canLockScreen || !this._actions.canSuspend)
            return;
        this._pending = true;
        try {
            await this._checkCompat();
            // Recheck after the asynchronous status query. Never substitute
            // logind suspend, an unlocked blank, or a compositor power cycle.
            if (!this._actions?.canLockScreen || !this._actions.canSuspend ||
                Main.sessionMode.isLocked || Main.sessionMode.isGreeter)
                return;
            console.log('Backlight-only Suspend: invoking the GNOME lock action');
            this._actions.activateLockScreen();
        } finally {
            this._pending = false;
        }
    }

    disable() {
        this._cancellable?.cancel();
        for (const process of this._processes ?? [])
            process.force_exit();
        for (const timeout of this._timeouts ?? [])
            GLib.Source.remove(timeout);
        this._timeouts?.clear();
        if (this._lockSignal)
            this._actions.disconnect(this._lockSignal);
        this._lockSignal = null;
        this._injections?.clear();
        this._injections = null;
        this._actions?._updateSuspend();
        this._actions = null;
        this._pending = false;
    }
}
