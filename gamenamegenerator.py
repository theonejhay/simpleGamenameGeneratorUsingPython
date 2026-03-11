from PyQt5 import QtCore, QtGui, QtWidgets
import random
import sys

# ─── Game Data ────────────────────────────────────────────────────────────────

ENEMIES = [
    {"name": "Rookie Grunt",   "hp": 30,  "atk": 5,  "reward": 10, "emoji": "👾"},
    {"name": "Armored Soldier","hp": 55,  "atk": 10, "reward": 20, "emoji": "🤖"},
    {"name": "Sniper Bot",     "hp": 40,  "atk": 14, "reward": 25, "emoji": "🎯"},
    {"name": "Tank Unit",      "hp": 90,  "atk": 8,  "reward": 35, "emoji": "🦾"},
    {"name": "BOSS: Overlord", "hp": 150, "atk": 18, "reward": 75, "emoji": "💀"},
]

GUN_TIERS = [
    {"name": "Rusty Pistol",      "dmg": (5, 12),  "cost": 0,   "ammo": 999},
    {"name": "Combat Rifle",      "dmg": (10, 20), "cost": 50,  "ammo": 20},
    {"name": "Plasma SMG",        "dmg": (15, 28), "cost": 100, "ammo": 15},
    {"name": "Shadow Sniper",     "dmg": (25, 50), "cost": 200, "ammo": 8},
    {"name": "Void Launcher",     "dmg": (40, 80), "cost": 400, "ammo": 5},
]

DARK_STYLE = """
QWidget          { background-color: #0d0d1a; color: #dde4f0; font-family: Consolas, monospace; }
QLabel           { color: #dde4f0; }
QProgressBar     {
    border: 1px solid #2a2a4a; border-radius: 4px;
    background: #0d0d1a; text-align: center; font-size: 10px; color: #fff;
}
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #e94560, stop:1 #ff6b6b); border-radius: 4px; }
QPushButton      {
    background-color: #1a1a3a; color: #a0c4ff; border: 1px solid #2a3a6a;
    border-radius: 5px; padding: 6px 14px; font-size: 11px; font-family: Consolas, monospace;
}
QPushButton:hover   { background-color: #2a2a5a; border-color: #e94560; color: #ffffff; }
QPushButton:pressed { background-color: #e94560; color: #ffffff; }
QPushButton:disabled{ background-color: #111128; color: #444; border-color: #222; }
QTextEdit        {
    background-color: #07071a; border: 1px solid #1a1a3a; border-radius: 4px;
    color: #7affb2; font-family: Consolas, monospace; font-size: 10px;
}
QComboBox        {
    background-color: #1a1a3a; border: 1px solid #2a3a6a; border-radius: 4px;
    padding: 4px 8px; color: #a0c4ff; font-family: Consolas, monospace; font-size: 11px;
}
QComboBox QAbstractItemView { background-color: #1a1a3a; color: #a0c4ff; selection-background-color: #e94560; }
"""

# ─── Main Window ──────────────────────────────────────────────────────────────

class GunGame(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("☠  New Mission ☠")
        self.setFixedSize(620, 680)
        self.setStyleSheet(DARK_STYLE)

        # Player state
        self.player_max_hp   = 100
        self.player_hp       = 100
        self.player_coins    = 0
        self.player_gun_idx  = 0
        self.player_ammo     = 999   # rusty pistol has infinite
        self.wave            = 0
        self.enemy           = None
        self.enemy_hp        = 0
        self.enemy_max_hp    = 0
        self.in_combat       = False

        self._build_ui()
        self._start_new_wave()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(14, 14, 14, 14)

        # ── Title ──
        title = QtWidgets.QLabel("☠  Enemy Appear  ☠")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; color: #e94560; font-weight: bold; letter-spacing: 3px; padding: 4px;")
        root.addWidget(title)

        # ── Status bar ──
        status_row = QtWidgets.QHBoxLayout()

        self.lbl_wave = QtWidgets.QLabel("WAVE 1")
        self.lbl_wave.setStyleSheet("color:#ffcc44; font-size:12px; font-weight:bold;")

        self.lbl_coins = QtWidgets.QLabel("💰 0")
        self.lbl_coins.setStyleSheet("color:#ffdd88; font-size:12px;")

        self.lbl_gun = QtWidgets.QLabel("🔫 Rusty Pistol  ∞ ammo")
        self.lbl_gun.setStyleSheet("color:#a0c4ff; font-size:11px;")

        status_row.addWidget(self.lbl_wave)
        status_row.addStretch()
        status_row.addWidget(self.lbl_coins)
        status_row.addSpacing(20)
        status_row.addWidget(self.lbl_gun)
        root.addLayout(status_row)

        # ── HP bars ──
        bars_widget = QtWidgets.QWidget()
        bars_layout = QtWidgets.QGridLayout(bars_widget)
        bars_layout.setContentsMargins(0, 0, 0, 0)

        bars_layout.addWidget(QtWidgets.QLabel("YOU"), 0, 0)
        self.bar_player = QtWidgets.QProgressBar()
        self.bar_player.setMaximum(self.player_max_hp)
        self.bar_player.setValue(self.player_hp)
        self.bar_player.setFormat("%v / %m HP")
        self.bar_player.setFixedHeight(18)
        bars_layout.addWidget(self.bar_player, 0, 1)

        bars_layout.addWidget(QtWidgets.QLabel("ENEMY"), 1, 0)
        self.bar_enemy = QtWidgets.QProgressBar()
        self.bar_enemy.setMaximum(100)
        self.bar_enemy.setValue(0)
        self.bar_enemy.setFormat("— —")
        self.bar_enemy.setFixedHeight(18)
        self.bar_enemy.setStyleSheet(
            "QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #55cc55, stop:1 #88ff88); border-radius:4px; }"
        )
        bars_layout.addWidget(self.bar_enemy, 1, 1)

        root.addWidget(bars_widget)

        # ── Enemy portrait area ──
        enemy_card = QtWidgets.QFrame()
        enemy_card.setStyleSheet("background:#07071a; border:1px solid #1a1a3a; border-radius:8px; padding:6px;")
        enemy_card_lay = QtWidgets.QVBoxLayout(enemy_card)

        self.lbl_enemy_name = QtWidgets.QLabel("...")
        self.lbl_enemy_name.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_enemy_name.setStyleSheet("font-size:22px; color:#ff6b6b; font-weight:bold; letter-spacing:1px;")

        self.lbl_enemy_emoji = QtWidgets.QLabel("❓")
        self.lbl_enemy_emoji.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_enemy_emoji.setStyleSheet("font-size:56px;")

        enemy_card_lay.addWidget(self.lbl_enemy_emoji)
        enemy_card_lay.addWidget(self.lbl_enemy_name)
        root.addWidget(enemy_card)

        # ── Combat log ──
        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(140)
        root.addWidget(self.log)

        # ── Action buttons ──
        btn_row1 = QtWidgets.QHBoxLayout()
        self.btn_shoot   = self._btn("🔫  SHOOT",   self._action_shoot)
        self.btn_reload  = self._btn("🔄  RELOAD",  self._action_reload)
        self.btn_heal    = self._btn("💊  HEAL (30g)", self._action_heal)
        btn_row1.addWidget(self.btn_shoot)
        btn_row1.addWidget(self.btn_reload)
        btn_row1.addWidget(self.btn_heal)
        root.addLayout(btn_row1)

        btn_row2 = QtWidgets.QHBoxLayout()
        self.btn_upgrade = self._btn("⬆  UPGRADE GUN", self._action_upgrade)
        self.btn_next    = self._btn("➡  NEXT WAVE",   self._start_new_wave)
        self.btn_next.setEnabled(False)
        btn_row2.addWidget(self.btn_upgrade)
        btn_row2.addWidget(self.btn_next)
        root.addLayout(btn_row2)

        # ── Restart (hidden until game over) ──
        self.btn_restart = self._btn("🔁  PLAY AGAIN", self._restart)
        self.btn_restart.setStyleSheet(
            "QPushButton { background:#e94560; color:#fff; font-size:13px; font-weight:bold; border-radius:6px; padding:8px; }"
            "QPushButton:hover { background:#c73652; }"
        )
        self.btn_restart.hide()
        root.addWidget(self.btn_restart)

    def _btn(self, text, slot):
        b = QtWidgets.QPushButton(text)
        b.clicked.connect(slot)
        b.setFixedHeight(34)
        return b

    # ── Game Logic ────────────────────────────────────────────────────────────

    def _start_new_wave(self):
        self.wave += 1
        idx = min(self.wave - 1, len(ENEMIES) - 1)
        # Scale enemy for higher waves
        base = ENEMIES[idx].copy()
        scale = 1 + (self.wave - 1) * 0.15
        self.enemy         = base
        self.enemy_max_hp  = int(base["hp"] * scale)
        self.enemy_hp      = self.enemy_max_hp
        self.in_combat     = True

        self.btn_next.setEnabled(False)
        self.btn_shoot.setEnabled(True)
        self.btn_reload.setEnabled(True)

        self.lbl_wave.setText(f"WAVE {self.wave}")
        self.lbl_enemy_name.setText(f"{base['emoji']}  {base['name']}")
        self.lbl_enemy_emoji.setText(base["emoji"])

        self.bar_enemy.setMaximum(self.enemy_max_hp)
        self.bar_enemy.setValue(self.enemy_max_hp)
        self.bar_enemy.setFormat(f"%v / {self.enemy_max_hp} HP")

        self._log(f"\n⚠  Wave {self.wave}: {base['name']} appears!", "#ffcc44")
        self._log(f"   ATK: {int(base['atk']*scale)}  HP: {self.enemy_max_hp}  Reward: {int(base['reward']*scale)}g", "#aaa")
        self._refresh_status()

    def _action_shoot(self):
        if not self.in_combat:
            return
        gun = GUN_TIERS[self.player_gun_idx]

        # Check ammo
        if self.player_ammo == 0:
            self._log("⚡  OUT OF AMMO! Press RELOAD.", "#ff4444")
            return

        if self.player_ammo != 999:
            self.player_ammo -= 1

        # Player attacks
        dmg = random.randint(*gun["dmg"])
        crit = random.random() < 0.15
        if crit:
            dmg = int(dmg * 1.8)
        self.enemy_hp = max(0, self.enemy_hp - dmg)
        self.bar_enemy.setValue(self.enemy_hp)

        hit_txt = f"💥  CRITICAL HIT! " if crit else "🔫  You shot  "
        self._log(f"{hit_txt}→ {self.enemy['name']} for {dmg} dmg  (HP: {self.enemy_hp}/{self.enemy_max_hp})", "#7affb2")

        if self.enemy_hp <= 0:
            self._enemy_defeated()
            return

        # Enemy counter-attacks
        scale = 1 + (self.wave - 1) * 0.15
        e_atk = int(self.enemy["atk"] * scale)
        dodge = random.random() < 0.1
        if dodge:
            self._log("⚡  You DODGED the attack!", "#a0c4ff")
        else:
            self.player_hp = max(0, self.player_hp - e_atk)
            self.bar_player.setValue(self.player_hp)
            self._log(f"💢  {self.enemy['name']} hits you for {e_atk}  (HP: {self.player_hp}/{self.player_max_hp})", "#ff6b6b")

        self._refresh_status()

        if self.player_hp <= 0:
            self._game_over()

    def _action_reload(self):
        gun = GUN_TIERS[self.player_gun_idx]
        if gun["ammo"] == 999:
            self._log("♾  Rusty Pistol never needs reloading.", "#aaa")
            return
        self.player_ammo = gun["ammo"]
        self._log(f"🔄  Reloaded! Ammo: {self.player_ammo}", "#a0c4ff")
        self._refresh_status()

    def _action_heal(self):
        cost = 30
        if self.player_coins < cost:
            self._log(f"💰  Need {cost}g to heal. You have {self.player_coins}g.", "#ff4444")
            return
        heal = 35
        self.player_coins -= cost
        self.player_hp = min(self.player_max_hp, self.player_hp + heal)
        self.bar_player.setValue(self.player_hp)
        self._log(f"💊  Healed +{heal} HP  (HP: {self.player_hp}/{self.player_max_hp})", "#88ff88")
        self._refresh_status()

    def _action_upgrade(self):
        next_idx = self.player_gun_idx + 1
        if next_idx >= len(GUN_TIERS):
            self._log("🏆  Already using the best gun!", "#ffcc44")
            return
        cost = GUN_TIERS[next_idx]["cost"]
        if self.player_coins < cost:
            self._log(f"💰  Need {cost}g for {GUN_TIERS[next_idx]['name']}. Have {self.player_coins}g.", "#ff4444")
            return
        self.player_coins -= cost
        self.player_gun_idx = next_idx
        gun = GUN_TIERS[self.player_gun_idx]
        self.player_ammo = gun["ammo"]
        self._log(f"⬆  Upgraded to {gun['name']}!  DMG: {gun['dmg'][0]}-{gun['dmg'][1]}", "#ffdd88")
        self._refresh_status()

    def _enemy_defeated(self):
        scale = 1 + (self.wave - 1) * 0.15
        reward = int(self.enemy["reward"] * scale)
        self.player_coins += reward
        self.in_combat = False
        self.btn_shoot.setEnabled(False)
        self.btn_next.setEnabled(True)
        self.lbl_enemy_emoji.setText("💥")
        self._log(f"\n✅  {self.enemy['name']} DEFEATED!  +{reward}g", "#ffcc44")

        if self.wave >= 5:
            self._log("\n🏆  YOU CLEARED ALL WAVES! YOU WIN!", "#ffdd00")
            self.btn_next.setEnabled(False)
            self.btn_restart.show()

        self._refresh_status()

    def _game_over(self):
        self.in_combat = False
        self.btn_shoot.setEnabled(False)
        self.btn_reload.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.lbl_enemy_emoji.setText("💀")
        self._log("\n☠  GAME OVER — YOU DIED.", "#e94560")
        self.btn_restart.show()

    def _restart(self):
        self.player_hp      = self.player_max_hp
        self.player_coins   = 0
        self.player_gun_idx = 0
        self.player_ammo    = 999
        self.wave           = 0
        self.in_combat      = False
        self.btn_restart.hide()
        self.btn_shoot.setEnabled(True)
        self.btn_reload.setEnabled(True)
        self.bar_player.setValue(self.player_max_hp)
        self.log.clear()
        self._start_new_wave()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _log(self, text, color="#dde4f0"):
        self.log.setTextColor(QtGui.QColor(color))
        self.log.append(text)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def _refresh_status(self):
        self.lbl_coins.setText(f"💰 {self.player_coins}g")
        gun = GUN_TIERS[self.player_gun_idx]
        ammo_str = "∞" if self.player_ammo == 999 else str(self.player_ammo)
        self.lbl_gun.setText(f"🔫 {gun['name']}  [{ammo_str} ammo]")


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = GunGame()
    window.show()
    sys.exit(app.exec_())
