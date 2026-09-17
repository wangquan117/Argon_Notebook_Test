#!/bin/bash
#
# restore_pi_shutdown.sh
#
# 修复树莓派 5 安装 argon1v5.sh 后「关机选项」消失，且官方卸载后仍不恢复的问题。
#
# 根因说明（为何卸载脚本不够）：
# 1. argon1v5.sh 会启动 argononed，用 libgpiod 独占 GPIO4（机箱 MCU 电源键脉冲）。
#    官方 argonone-uninstall 只删 /etc/argon 和 systemd 服务，不还原桌面组件。
# 2. 安装过程会执行 apt-get upgrade（不是 full-upgrade）。这会把 wf-panel-pi /
#    pishutdown / raspberrypi-ui-mods 留在 held-back 或不匹配状态，
#    树莓派桌面菜单里的「Shutdown...」会消失或点了没反应。
#    卸载不会回滚这次系统升级。
# 3. 机箱电源键不是 Pi 5 板载 J2 电源键。MCU 只在 GPIO4 上打 20–50ms 脉冲。
#    没有 argononed 时，GPIO4 不会变成 KEY_POWER，所以系统关机对话框也不会弹出。
#    新系统能看到关机选项，是因为桌面菜单 / 板载电源键走 pishutdown，不依赖 GPIO4。
#
# 在出问题的树莓派上执行：
#   chmod +x restore_pi_shutdown.sh
#   ./restore_pi_shutdown.sh              # 诊断 + 清理残留 + 修复桌面关机菜单
#   ./restore_pi_shutdown.sh --map-gpio4  # 额外把 GPIO4 映射成电源键，让机箱按键弹出关机对话框
#   ./restore_pi_shutdown.sh --diagnose   # 只诊断，不改系统
#   ./restore_pi_shutdown.sh --skip-apt   # 不跑 apt 升级（只清 Argon 残留 / 还原面板配置）
#
# 修复后必须重启。若以后再次安装 argon1v5.sh，请先去掉 gpio-shutdown overlay，
# 否则会和 argononed 抢 GPIO4。
#

set -u

DO_DIAGNOSE_ONLY=0
DO_MAP_GPIO4=0
DO_SKIP_APT=0
NEED_REBOOT=0

for arg in "$@"; do
	case "$arg" in
		--diagnose|-n) DO_DIAGNOSE_ONLY=1 ;;
		--map-gpio4|--gpio4) DO_MAP_GPIO4=1 ;;
		--skip-apt) DO_SKIP_APT=1 ;;
		-h|--help)
			sed -n '2,26p' "$0"
			exit 0
			;;
	esac
done

export DEBIAN_FRONTEND=noninteractive

if [ "$(id -u)" -eq 0 ]; then
	SUDO=""
else
	SUDO="sudo"
fi

if [ -e /boot/firmware/config.txt ]; then
	CONFIG=/boot/firmware/config.txt
elif [ -e /boot/config.txt ]; then
	CONFIG=/boot/config.txt
else
	CONFIG=""
fi

REAL_USER="${SUDO_USER:-${USER:-pi}}"
if [ "$REAL_USER" = "root" ]; then
	if [ -d /home/pi ]; then
		REAL_USER=pi
	else
		REAL_USER="$(awk -F: '$3>=1000 && $1!="nobody" {print $1; exit}' /etc/passwd)"
	fi
fi
REAL_HOME="$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f6)"
[ -n "$REAL_HOME" ] || REAL_HOME="/home/$REAL_USER"

say() { printf '%s\n' "$*"; }
ok() { printf '  [OK] %s\n' "$*"; }
warn() { printf '  [!!] %s\n' "$*"; }
info() { printf '  [--] %s\n' "$*"; }

is_pi() {
	[ -f /proc/device-tree/model ] || return 1
	grep -qi "raspberry pi" /proc/device-tree/model 2>/dev/null
}

maybe_run() {
	if [ "$DO_DIAGNOSE_ONLY" -eq 1 ]; then
		info "diagnose-only, skip: $*"
		return 0
	fi
	eval "$@"
}

backup_file() {
	local f="$1"
	[ -f "$f" ] || return 0
	local bak="${f}.bak.$(date +%Y%m%d%H%M%S)"
	$SUDO cp -a "$f" "$bak"
	info "backup $f -> $bak"
}

# ---------------------------------------------------------------------------
# Diagnose
# ---------------------------------------------------------------------------
say "=============================================="
say " Raspberry Pi shutdown restore / diagnose"
say "=============================================="
say "user=$REAL_USER home=$REAL_HOME config=${CONFIG:-missing}"
if [ -f /proc/device-tree/model ]; then
	say "model=$(tr -d '\0' </proc/device-tree/model)"
fi
say

say "== leftover Argon files / services =="
LEFTOVER=0
for f in \
	/etc/argon \
	/lib/systemd/system/argononed.service \
	/lib/systemd/system/argoneond.service \
	/lib/systemd/system/argononeupd.service \
	/lib/systemd/system-shutdown/argon-shutdown.sh \
	/usr/bin/argon-config \
	/usr/bin/argonone-config \
	/usr/bin/argonone-uninstall \
	/etc/argononed.conf \
	"$REAL_HOME/Desktop/argonone-config.desktop"
do
	if [ -e "$f" ]; then
		warn "still present: $f"
		LEFTOVER=1
	else
		ok "gone: $f"
	fi
done

if command -v systemctl >/dev/null 2>&1; then
	if systemctl is-active --quiet argononed.service 2>/dev/null; then
		warn "argononed.service is still ACTIVE (holds GPIO4)"
		LEFTOVER=1
	else
		ok "argononed.service is not active"
	fi
fi

if command -v gpioinfo >/dev/null 2>&1; then
	GPIO_HOLD="$(gpioinfo gpiochip4 2>/dev/null | grep -E 'line +4:' || true)"
	if [ -z "$GPIO_HOLD" ]; then
		GPIO_HOLD="$(gpioinfo gpiochip0 2>/dev/null | grep -E 'line +4:' || true)"
	fi
	if echo "$GPIO_HOLD" | grep -qi argon; then
		warn "GPIO4 still claimed by argon: $GPIO_HOLD"
		LEFTOVER=1
	elif [ -n "$GPIO_HOLD" ]; then
		info "GPIO4: $GPIO_HOLD"
	else
		info "gpioinfo available, GPIO4 line not found (ok if overlay unused)"
	fi
else
	info "gpioinfo not installed (optional: sudo apt install gpiod)"
fi

say
say "== boot config overlays that affect power / USB =="
if [ -n "$CONFIG" ]; then
	grep -nE '^(dtoverlay|dtparam)=.*(gpio-shutdown|gpio-poweroff|gpio-key|dwc2|uart0|i2c_arm|nvme|pciex1|usb_max_current)' "$CONFIG" 2>/dev/null \
		| sed 's/^/  /' || info "no matching overlay lines"
	if grep -qE '^dtoverlay=gpio-poweroff' "$CONFIG"; then
		warn "gpio-poweroff overlay is set; this can break boot/shutdown behaviour"
	fi
else
	warn "config.txt not found"
fi

say
say "== desktop shutdown UI packages =="
for pkg in wf-panel-pi raspberrypi-ui-mods pishutdown lxpanel lxsession; do
	if dpkg-query -W -f='${Status} ${Version}\n' "$pkg" 2>/dev/null | grep -q "installed"; then
		ok "$pkg: $(dpkg-query -W -f='${Version}' "$pkg" 2>/dev/null)"
	else
		info "$pkg: not installed"
	fi
done

if command -v apt-mark >/dev/null 2>&1; then
	HELD="$(apt-mark showhold 2>/dev/null | tr '\n' ' ')"
	if [ -n "$HELD" ]; then
		warn "held packages: $HELD"
	fi
fi

UPGRADABLE="$(apt list --upgradable 2>/dev/null | grep -Ei 'wf-panel-pi|raspberrypi-ui-mods|pishutdown|lxpanel' || true)"
if [ -n "$UPGRADABLE" ]; then
	warn "held-back / upgradable desktop packages:"
	printf '%s\n' "$UPGRADABLE" | sed 's/^/    /'
else
	ok "no pending upgrades for panel/shutdown packages (or apt cache empty)"
fi

PISHUTDOWN_BIN=""
for c in /usr/bin/pishutdown /usr/bin/lxde-pi-shutdown-helper /usr/bin/wlogout; do
	if [ -x "$c" ]; then
		PISHUTDOWN_BIN="$c"
		ok "shutdown helper: $c"
		break
	fi
done
if [ -z "$PISHUTDOWN_BIN" ]; then
	warn "pishutdown / lxde-pi-shutdown-helper not found"
fi

UI_FILE="/usr/share/pishutdown/ui/pishutdown.ui"
if [ -f "$UI_FILE" ]; then
	if grep -A6 'id="btn_shutdown"' "$UI_FILE" | grep -qi '>False<'; then
		warn "pishutdown.ui hides btn_shutdown (visible=False)"
	else
		ok "pishutdown.ui shutdown button is not hidden"
	fi
else
	info "pishutdown.ui not present (newer images may embed the dialog)"
fi

say
say "== logind power-key policy =="
if [ -f /etc/systemd/logind.conf ]; then
	grep -E '^HandlePowerKey' /etc/systemd/logind.conf 2>/dev/null | sed 's/^/  /' \
		|| info "HandlePowerKey uses systemd default"
else
	info "logind.conf missing"
fi
if command -v systemd-inhibit >/dev/null 2>&1; then
	INHIB="$(systemd-inhibit --list 2>/dev/null | grep -i handle-power-key || true)"
	if [ -n "$INHIB" ]; then
		warn "power-key inhibitors:"
		printf '%s\n' "$INHIB" | sed 's/^/    /'
	else
		ok "no handle-power-key inhibitors listed"
	fi
fi

if [ "$DO_DIAGNOSE_ONLY" -eq 1 ]; then
	say
	say "Diagnose only. Re-run without --diagnose to apply fixes."
	exit 0
fi

if ! is_pi; then
	say
	warn "This host is not a Raspberry Pi. Refusing to change boot/desktop files."
	warn "Copy this script to the Pi and run it there."
	exit 1
fi

# ---------------------------------------------------------------------------
# 1. Remove leftover Argon userspace (uninstall is incomplete)
# ---------------------------------------------------------------------------
say
say "== cleaning leftover Argon userspace =="
if command -v argonone-uninstall >/dev/null 2>&1 && [ -x /etc/argon/argon-uninstall.sh ]; then
	info "official uninstall still present; removing files directly (non-interactive)"
fi

maybe_run "$SUDO systemctl stop argononed.service argononeupd.service argoneond.service argononeupsd.service argonupsrtcd.service 2>/dev/null || true"
maybe_run "$SUDO systemctl disable argononed.service argononeupd.service argoneond.service argononeupsd.service argonupsrtcd.service 2>/dev/null || true"
maybe_run "$SUDO systemctl --user stop argononeupduser.service 2>/dev/null || true"
maybe_run "$SUDO systemctl --user disable argononeupduser.service 2>/dev/null || true"

for f in \
	/lib/systemd/system/argononed.service \
	/lib/systemd/system/argoneond.service \
	/lib/systemd/system/argononeupd.service \
	/lib/systemd/system/argononeupsd.service \
	/lib/systemd/system/argonupsrtcd.service \
	/etc/systemd/user/argononeupduser.service \
	/lib/systemd/system-shutdown/argon-shutdown.sh \
	/usr/bin/argon-config \
	/usr/bin/argonone-config \
	/usr/bin/argonone-uninstall \
	/usr/bin/argonone-ir
do
	if [ -e "$f" ]; then
		maybe_run "$SUDO rm -f '$f'"
		ok "removed $f"
		NEED_REBOOT=1
	fi
done

for f in /etc/argonunits.conf /etc/argononed.conf /etc/argononed-hdd.conf /etc/argoneonrtc.conf /etc/argoneonoled.conf /etc/argonupsrtc.conf /etc/argononeupd.conf; do
	if [ -f "$f" ]; then
		maybe_run "$SUDO rm -f '$f'"
		ok "removed $f"
	fi
done

if [ -d /etc/argon ]; then
	maybe_run "$SUDO rm -rf /etc/argon"
	ok "removed /etc/argon"
	NEED_REBOOT=1
fi

if [ -f "$REAL_HOME/Desktop/argonone-config.desktop" ]; then
	maybe_run "rm -f '$REAL_HOME/Desktop/argonone-config.desktop'"
	ok "removed desktop shortcut"
fi

maybe_run "$SUDO systemctl daemon-reload"
ok "argon userspace leftover cleanup done"

# ---------------------------------------------------------------------------
# 2. Repair Raspberry Pi OS Shutdown menu (pishutdown / wf-panel-pi)
# ---------------------------------------------------------------------------
say
say "== repairing desktop Shutdown menu =="
if [ "$DO_SKIP_APT" -eq 1 ]; then
	info "skipping apt (passed --skip-apt)"
elif command -v apt-get >/dev/null 2>&1; then
	# argon1v5.sh uses apt-get upgrade, which leaves desktop packages held back.
	# full-upgrade is the known fix for a missing / dead Shutdown... menu item.
	maybe_run "$SUDO apt-get update -y"
	maybe_run "$SUDO apt-get -y --with-new-pkgs upgrade"
	maybe_run "$SUDO apt-get -y full-upgrade"
fi

if [ "$DO_SKIP_APT" -eq 1 ]; then
	info "skipping package reinstall (passed --skip-apt)"
else
	REINSTALL_PKGS=()
	for pkg in wf-panel-pi raspberrypi-ui-mods pishutdown; do
		if dpkg-query -W "$pkg" >/dev/null 2>&1; then
			REINSTALL_PKGS+=("$pkg")
		fi
	done
	if [ "${#REINSTALL_PKGS[@]}" -gt 0 ]; then
		maybe_run "$SUDO apt-get install --reinstall -y ${REINSTALL_PKGS[*]}"
		ok "reinstalled: ${REINSTALL_PKGS[*]}"
		NEED_REBOOT=1
	else
		warn "desktop UI packages not found; this image may not include the graphical Shutdown menu"
	fi
fi

if [ -f "$UI_FILE" ]; then
	if grep -A8 'id="btn_shutdown"' "$UI_FILE" | grep -qi '>False<'; then
		backup_file "$UI_FILE"
		if [ "$DO_DIAGNOSE_ONLY" -eq 0 ]; then
			$SUDO python3 -c 'from pathlib import Path; import re
p = Path("/usr/share/pishutdown/ui/pishutdown.ui")
text = p.read_text()
text2 = re.sub(
    r"(id=\"btn_shutdown\"[\s\S]{0,400}?<property name=\"visible\">)False(</property>)",
    r"\1True\2",
    text,
    count=1,
)
p.write_text(text2 if text2 != text else text)
print("restored btn_shutdown visible=True" if text2 != text else "btn_shutdown pattern mismatch")
'
			NEED_REBOOT=1
		fi
	fi
fi

# User panel copies survive argon uninstall and can drop the menu plugin.
PANEL_RESET=0
for panel in \
	"$REAL_HOME/.config/wf-panel-pi.ini" \
	"$REAL_HOME/.config/wf-panel-pi/wf-panel-pi.ini"
do
	if [ -f "$panel" ]; then
		backup_file "$panel"
		maybe_run "rm -f '$panel'"
		ok "reset $panel (will be recreated from defaults on next login)"
		PANEL_RESET=1
		NEED_REBOOT=1
	fi
done
if [ -d "$REAL_HOME/.config/lxpanel" ]; then
	backup_file "$REAL_HOME/.config/lxpanel/LXDE-pi/panels/panel"
	info "user lxpanel config exists; leaving it in place (backup created if present)"
	info "if Shutdown is still missing after reboot, remove ~/.config/lxpanel and re-login"
fi

# Default logind: let the desktop show the dialog instead of instant poweroff.
if [ -f /etc/systemd/logind.conf ]; then
	if grep -qE '^HandlePowerKey=' /etc/systemd/logind.conf; then
		backup_file /etc/systemd/logind.conf
		maybe_run "$SUDO sed -i 's/^HandlePowerKey=/#HandlePowerKey=/' /etc/systemd/logind.conf"
		ok "commented custom HandlePowerKey (desktop dialog can appear again)"
		NEED_REBOOT=1
	fi
fi

# ---------------------------------------------------------------------------
# 3. Optional: map Argon GPIO4 pulses to KEY_POWER (OS shutdown dialog)
# ---------------------------------------------------------------------------
if [ "$DO_MAP_GPIO4" -eq 1 ] && [ -n "$CONFIG" ]; then
	say
	say "== mapping GPIO4 to KEY_POWER (case button -> shutdown dialog) =="
	if grep -qE '^dtoverlay=gpio-poweroff' "$CONFIG"; then
		backup_file "$CONFIG"
		maybe_run "$SUDO sed -i 's/^dtoverlay=gpio-poweroff/#dtoverlay=gpio-poweroff/' '$CONFIG'"
		warn "disabled gpio-poweroff (conflicts with normal shutdown)"
	fi
	if grep -qE '^dtoverlay=gpio-shutdown' "$CONFIG"; then
		ok "gpio-shutdown overlay already present"
	else
		backup_file "$CONFIG"
		if [ "$DO_DIAGNOSE_ONLY" -eq 0 ]; then
			printf '\n# Added by restore_pi_shutdown.sh --map-gpio4\n# Argon MCU pulses GPIO4; this overlay turns it into KEY_POWER.\n# Remove these lines if you reinstall argon1v5.sh.\ndtoverlay=gpio-shutdown,gpio_pin=4,active_low=1,gpio_pull=down\n' \
				| $SUDO tee -a "$CONFIG" >/dev/null
			ok "appended dtoverlay=gpio-shutdown for GPIO4"
			NEED_REBOOT=1
		fi
	fi
else
	info "case power button will not show the OS dialog unless you pass --map-gpio4"
	info "desktop menu Shutdown is independent of the case button"
fi

# Do not revert EEPROM PSU_MAX_CURRENT=5000 or NVMe/PCIe overlays.
# Those are intentional Argon V5 settings and do not hide the Shutdown menu.

say
say "=============================================="
say " Done."
if [ "$NEED_REBOOT" -eq 1 ]; then
	say " Reboot is required:  sudo reboot"
	say " After reboot, open the Raspberry menu; Shutdown... should be back."
	say " Shortcuts while the menu is still missing:"
	say "   Ctrl+Alt+Del     or     /usr/bin/pishutdown"
else
	say " No reboot-triggering change detected; reboot anyway if the menu is still gone."
fi
say "=============================================="
exit 0
