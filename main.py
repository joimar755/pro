import sys
import serial
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox
)
from PyQt6.QtCore import QTimer, Qt
from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Integer, String, create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:@localhost:3306/dht22"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session() 

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

class Sensor(Base):
    __tablename__ = "sensor_dht22"
    id = Column(Integer, primary_key=True)
    Temperatura = Column(String(255), nullable=False)
    Humedad = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

class ControlLeds(Base):
    __tablename__ = "leds"
    id = Column(Integer, primary_key=True)
    led1 = Column(Boolean, default=False, nullable=False)
    led2 = Column(Boolean, default=False, nullable=False)
    led3 = Column(Boolean, default=False, nullable=False)
    user_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

#Base.metadata.create_all(engine)

# Configuración del puerto serie
ser = serial.Serial("COM5", 115200, timeout=1)

# ================= Login =================
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔒 Login")
        self.setGeometry(300, 300, 300, 150)

        self.user_label = QLabel("Usuario:")
        self.user_input = QLineEdit()
        self.pass_label = QLabel("Contraseña:")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_btn = QPushButton("Ingresar")
        self.login_btn.clicked.connect(self.verificar_login)

        layout = QVBoxLayout()
        layout.addWidget(self.user_label)
        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_label)
        layout.addWidget(self.pass_input)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

    def verificar_login(self):
        usuario = self.user_input.text()
        contrasena = self.pass_input.text() 

        usuario = session.query(Usuario).filter_by(username=usuario, password=contrasena).first()
        print(usuario)

        # Aquí puedes poner tu usuario y contraseña reales
        if usuario:
            self.abrir_panel()
            return
        else:
            QMessageBox.warning(self, "Error", "Usuario o contraseña incorrectos")
            return

    def abrir_panel(self):
        self.control_panel = ControlPanel()
        self.control_panel.show()
        self.close()


# ================= Control Panel =================
class ControlPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("⚡ Control de LEDs y Sensor DHT22 - ESP32")
        self.setGeometry(200, 200, 400, 350)

        # Labels para mostrar datos
        self.temp_label = QLabel("🌡 Temperature: -- °C")
        self.hum_label = QLabel("💧 Humedad: -- %")
        self.led1_label = QLabel("LED1: APAGADO")
        self.led2_label = QLabel("LED2: APAGADO")
        self.led3_label = QLabel("LED3: APAGADO")

        for lbl in [self.temp_label, self.hum_label, self.led1_label, self.led2_label, self.led3_label]:
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        def prender():
            ser.write(b'1')
        
        def apagar():
            ser.write(b'0')

        def prenderDos():
            ser.write(b'2')
        
        def apagarDos():
            ser.write(b'3')
        
        def prenderTres():
            ser.write(b'4')
        
        def apagarTres():
            ser.write(b'5')



        # Botones LED1
        self.btn_led1_on = QPushButton("Encender LED1")
        self.btn_led1_off = QPushButton("Apagar LED1")
        self.btn_led1_on.clicked.connect(prender)
        self.btn_led1_off.clicked.connect(apagar)

        # Botones LED2
        self.btn_led2_on = QPushButton("Encender LED2")
        self.btn_led2_off = QPushButton("Apagar LED2")
        self.btn_led2_on.clicked.connect(prenderDos)
        self.btn_led2_off.clicked.connect(apagarDos)

        # Botones LED3
        self.btn_led3_on = QPushButton("Encender LED3")
        self.btn_led3_off = QPushButton("Apagar LED3")
        self.btn_led3_on.clicked.connect(prenderTres)
        self.btn_led3_off.clicked.connect(apagarTres)

        # Layout principal
        layout = QVBoxLayout()
        layout.addWidget(self.temp_label)
        layout.addWidget(self.hum_label)
        layout.addWidget(self.led1_label)
        layout.addWidget(self.led2_label)
        layout.addWidget(self.led3_label)

        # Agrupar botones
        layout.addLayout(self.crear_fila_botones(self.btn_led1_on, self.btn_led1_off))
        layout.addLayout(self.crear_fila_botones(self.btn_led2_on, self.btn_led2_off))
        layout.addLayout(self.crear_fila_botones(self.btn_led3_on, self.btn_led3_off))

        self.setLayout(layout)

        # Timer para refrescar datos del puerto serie
        self.timer = QTimer()
        self.timer.timeout.connect(self.leer_serial)
        self.timer.start(500)

    def crear_fila_botones(self, btn_on, btn_off):
        fila = QHBoxLayout()
        fila.addWidget(btn_on)
        fila.addWidget(btn_off)
        return fila

    def enviar_comando(self, comando):
        ser.write((comando + "\n").encode())

    def leer_serial(self):
        if ser.in_waiting > 0:
            try:
                linea = ser.readline().decode(errors="ignore").strip()
                print("DEBUG ->", linea)  # 👈 Para que veas lo que llega

                if "Humidite:" in linea and "Temperature:" in linea:
                    # Ejemplo de línea: "Humidite: 60% Temperature: 25°C, 77°F"
                    partes = linea.split()
                    hum = partes[1].replace("%", "")       # 60
                    temp = partes[3].replace("°C,", "")    # 25
                    self.hum_label.setText(f"💧 Humedad: {hum} %")
                    self.temp_label.setText(f"🌡 Temperature: {temp} °C")

                elif "LED1 ENCENDIDO" in linea:
                    self.led1_label.setText("LED1: ENCENDIDO")
                elif "LED1 APAGADO" in linea:
                    self.led1_label.setText("LED1: APAGADO")
                elif "LED2 ENCENDIDO" in linea:
                    self.led2_label.setText("LED2: ENCENDIDO")
                elif "LED2 APAGADO" in linea:
                    self.led2_label.setText("LED2: APAGADO")
                elif "LED3 ENCENDIDO" in linea:
                    self.led3_label.setText("LED3: ENCENDIDO")
                elif "LED3 APAGADO" in linea:
                    self.led3_label.setText("LED3: APAGADO")

            except Exception as e:
                print(f"Error leyendo serial: {e}")




# ================= Main =================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginWindow()
    login.show()
    sys.exit(app.exec())
