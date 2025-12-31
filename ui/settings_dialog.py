from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QComboBox, 
                            QLineEdit, QDialogButtonBox, QLabel, QDoubleSpinBox, QSpinBox)
from utils.config_manager import get_config_manager
import os

class SettingsDialog(QDialog):
    """
    Dialog to manage application settings.
    Edits the configuration via ConfigManager.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedWidth(400)
        
        self.config = get_config_manager()
        
        # Set Dialog Icon
        from PyQt5.QtGui import QIcon
        icon_path = self.config.get_resource_path('icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setup_ui()
        self.load_values()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Language Selection
        self.combo_lang = QComboBox()
        self.combo_lang.setToolTip("Language of your Kindle 'My Clippings.txt' file.")
        
        # Load languages dynamically
        import json
        lang_file = self.config.get_resource_path('languages.json')
        
        loaded_langs = ["auto"]
        if os.path.exists(lang_file):
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    loaded_langs.extend(list(data.keys()))
            except Exception as e:
                print(f"Error loading languages: {e}")
                # Fallback if JSON fails
                loaded_langs.extend(["es", "en", "fr", "de", "it", "pt"])
        else:
            loaded_langs.extend(["es", "en", "fr", "de", "it", "pt"])
            
        self.combo_lang.addItems(loaded_langs)
        
        # Default Creator
        self.txt_creator = QLineEdit()
        self.txt_creator.setToolTip("Author name stored in the Joplin note metadata.")
        
        # Default Notebook
        self.txt_notebook = QLineEdit()
        self.txt_notebook.setToolTip("Name of the root notebook created in Joplin imports.")

        # Default Output Filename
        self.txt_output = QLineEdit()
        self.txt_output.setPlaceholderText("import_clippings.jex")
        self.txt_output.setToolTip("Default filename for exported JEX files.")

        # Location (Lat, Long, Alt)
        self.spin_lat = QDoubleSpinBox()
        self.spin_lat.setRange(-90, 90)
        self.spin_lat.setDecimals(5)
        
        self.spin_long = QDoubleSpinBox()
        self.spin_long.setRange(-180, 180)
        self.spin_long.setDecimals(5)
        
        self.spin_alt = QSpinBox()
        self.spin_alt.setRange(-500, 10000)
        self.spin_alt.setSuffix(" m")

        form_layout.addRow("Kindle Language:", self.combo_lang)
        form_layout.addRow("Default Creator:", self.txt_creator)
        form_layout.addRow("Default Notebook:", self.txt_notebook)
        form_layout.addRow("Default Output Name:", self.txt_output)
        
        # Add a separator or label for Location
        lbl_loc = QLabel("<b>Geo Location (Optional)</b>")
        lbl_loc.setStyleSheet("margin-top: 10px; margin-bottom: 5px;")
        form_layout.addRow(lbl_loc)
        form_layout.addRow("Latitude:", self.spin_lat)
        form_layout.addRow("Longitude:", self.spin_long)
        form_layout.addRow("Altitude:", self.spin_alt)
        
        layout.addLayout(form_layout)
        
        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.save_settings)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def load_values(self):
        """Populate fields with current config."""
        lang = self.config.get("language", "es")
        index = self.combo_lang.findText(lang)
        if index >= 0:
            self.combo_lang.setCurrentIndex(index)
            
        self.txt_creator.setText(self.config.get("creator", "System"))
        self.txt_notebook.setText(self.config.get("notebook_title", "Kindle Imports"))
        self.txt_output.setText(self.config.get("output_file", "import_clippings"))
        
        # Load Location
        loc = self.config.get("location", [0.0, 0.0, 0])
        if len(loc) >= 3:
            self.spin_lat.setValue(float(loc[0]))
            self.spin_long.setValue(float(loc[1]))
            self.spin_alt.setValue(int(loc[2]))

    def save_settings(self):
        """Persist changes to config."""
        self.config.set("language", self.combo_lang.currentText())
        self.config.set("creator", self.txt_creator.text())
        self.config.set("notebook_title", self.txt_notebook.text())
        self.config.set("output_file", self.txt_output.text())
        
        # Save lat/long/alt as list
        loc = [self.spin_lat.value(), self.spin_long.value(), self.spin_alt.value()]
        self.config.set("location", loc)
        
        self.accept()
