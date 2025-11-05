""""""
from PyQt5.QtWidgets import QStatusBar, QLabel
from PyQt5.QtCore import Qt  # Import Qt for alignment


def statusMessage(window, item_status_tip, other=None):
    permanent_message_label = window.statusBar().findChild(QLabel, "permanentStatusLabel")

    if not permanent_message_label:
        permanent_message_label = QLabel()
        permanent_message_label.setMinimumWidth(100)
        permanent_message_label.setObjectName("permanentStatusLabel")  # Give it a unique object name for easy retrieval
        permanent_message_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Align to the LEFT
        window.statusBar().addWidget(permanent_message_label)  # Use addWidget() for left alignment
    current_temporary_message = window.statusBar().currentMessage()

    # Construct the message for the permanent label
    permanent_parts = [f"{window.condition}\t", f"REF:{window.frameref}\t"]

    new_permanent_text = f"{item_status_tip}"
    if other is not None:
        new_permanent_text += f" : {other}"

    # Set the text of the permanent label
    permanent_message_label.setText("   ".join(permanent_parts + [new_permanent_text]) + "\t")

    # If you want to ensure no *temporary* showMessage() is active, you can still clear it,
    # though with a left-aligned permanent widget, showMessage() messages might appear to its right.
    window.statusBar().clearMessage()


def setTitle(window, reg, proj, ver, itm="None"):
    window.setWindowTitle(f"LightCommander - {reg} - {proj} - {ver} - {itm}")

def term(time, text):
    print(f"[{time}] {text}")