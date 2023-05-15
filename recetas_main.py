import sys
import csv
import openai

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidgetItem
from PyQt5.QtGui import QMovie
from PyQt5.uic import loadUi


class ConsultaThread(QtCore.QThread):
    finalizada_lista = QtCore.pyqtSignal(str)
    finalizada_receta = QtCore.pyqtSignal(str)

    # Constructor
    def __init__(self, tipo_consulta, prompt):
        super().__init__()
        self.tipo_consulta = tipo_consulta
        self.prompt = prompt

    def run(self):
        # Configuración de OpenAI
        openai.api_key = \
        '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'
        
        # Realiza la solicitud a OpenAI
        response = openai.Completion.create(
            engine='text-davinci-002',
            prompt=self.prompt,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.1,
        )

        # Emite la señal con la respuesta
        if self.tipo_consulta == 0:
            self.finalizada_lista.emit(response.choices[0].text.strip())
        else:
            self.finalizada_receta.emit(response.choices[0].text.strip())

class VentanaPrincipal(QMainWindow):
    # Constructor
    def __init__(self):
        super(VentanaPrincipal, self).__init__()
        loadUi("recetas_mw.ui", self)

        self.lb_anim_lista.clear()
        self.lb_anim_receta.clear()
        self.movie = QMovie("loading.gif")

        self.obtener_ingredientes()
        self.bt_elim_ing.setEnabled(False)
        self.bt_gen_lista.setEnabled(False)
        self.bt_gen_receta.setEnabled(False)

        # EVENTOS
        self.cb_ingredientes.currentIndexChanged.connect(
            self.on_cb_ingredientes_currentIndexChanged
            )

        self.lw_ingredientes.itemSelectionChanged.connect(
            self.on_lw_ingredientes_itemSelectionChanged
            )

        self.lw_recetas.itemSelectionChanged.connect(
            self.on_lw_recetas_itemSelectionChanged
            )

        self.bt_add_ing.clicked.connect(self.agregar_ing)
        self.bt_elim_ing.clicked.connect(self.eliminar_ing)
        self.bt_gen_lista.clicked.connect(self.generar_lista_receta)
        self.bt_gen_receta.clicked.connect(self.generar_receta)
        
        self.bt_clear.clicked.connect(self.limpiar_campos)

        self.bt_salir.clicked.connect(
            QtCore.QCoreApplication.instance().quit
            )

    def obtener_ingredientes(self):
        self.cb_ingredientes.addItem('<Selecciona...>')

        with open('ingredientes.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)

            for row in reader:
                for field in row:
                    for word in field.split(','):
                        self.cb_ingredientes.addItem(word.strip())

    def on_lw_ingredientes_itemSelectionChanged(self):
        if self.lw_ingredientes.count() == 0 \
        or len(self.lw_ingredientes.selectedItems()) == 0:
            self.bt_elim_ing.setEnabled(False)
        else:
            self.bt_elim_ing.setEnabled(True)

        if self.lw_ingredientes.count() == 0:
            self.bt_gen_lista.setEnabled(False)
        else:
            self.bt_gen_lista.setEnabled(True)

    def on_lw_recetas_itemSelectionChanged(self):
        if self.lw_recetas.count() == 0 \
        or len(self.lw_recetas.selectedItems()) == 0:
            self.bt_gen_receta.setEnabled(False)
        else:
            self.bt_gen_receta.setEnabled(True)

    def on_cb_ingredientes_currentIndexChanged(self):
        if self.cb_ingredientes.currentText() == '<Selecciona...>':
            # Deshabilita el botón bt_add_ing
            self.bt_add_ing.setEnabled(False)
        else:
            # Habilita el botón bt_add_ing
            self.bt_add_ing.setEnabled(True)

    def eliminar_ing(self):
        selected_items = self.lw_ingredientes.selectedItems()
        
        for item in selected_items:
            row = self.lw_ingredientes.row(item)
            self.lw_ingredientes.takeItem(row)

        self.on_lw_ingredientes_itemSelectionChanged()

    def agregar_ing(self):
        ingrediente = self.cb_ingredientes.currentText()

        # Verifica si el ingrediente ya existe en lw_ingredientes
        exists = False
        for i in range(self.lw_ingredientes.count()):
            if self.lw_ingredientes.item(i).text() == ingrediente:
                exists = True
                break

        if not exists:
            self.lw_ingredientes.addItem(ingrediente)

        self.on_lw_ingredientes_itemSelectionChanged()

    def generar_lista_receta(self):
        self.lw_recetas.clear()

        # Obtener todos los elementos de 'lw_ingredientes'
        ingredientes = []
        for i in range(self.lw_ingredientes.count()):
            item = self.lw_ingredientes.item(i)
            ingredientes.append(item.text())

        prompt = f"Necesito una lista de como máximo 5 recetas (pueden ser \
        menos, pero no más de 5) que existan en la vida real que fuesen \
        posibles de elaborar teniendo los siguientes ingredientes: \
        {ingredientes}. Si no existen recetas coherentes con los ingredientes \
        proporcionados, respondeme 'No existen recetas'."

        self.consulta_thread = ConsultaThread(0, prompt)
        self.consulta_thread.finalizada_lista.connect(self.mostrar_lista_recetas)

        # Inicia la animación y la consulta en el hilo secundario
        self.iniciar_anim_lista()
        self.consulta_thread.start()

    def generar_receta(self):
        indice = self.lw_recetas.currentRow()
        receta = self.lw_recetas.item(indice)
        texto = receta.text()

        if texto != "No existen recetas":
            prompt = f"Necesito la siguiente receta de cocina detallada y \
            escrita en español con los ingredientes que usa, la cantidad de \
            cada uno, la elaboración de la receta, etc.): \
            {texto}."

            self.consulta_thread = ConsultaThread(1, prompt)
            self.consulta_thread.finalizada_receta.connect(self.mostrar_receta)

            # Inicia la animación y la consulta en el hilo secundario
            self.iniciar_anim_receta()
            self.consulta_thread.start()

    def mostrar_lista_recetas(self, respuesta):
        self.finalizar_anim_lista()

        lista_recetas = respuesta.splitlines()
        for i in lista_recetas:
            item = QListWidgetItem(i)
            self.lw_recetas.addItem(item)

    def mostrar_receta(self, respuesta):
        self.finalizar_anim_receta()
        self.te_receta.setPlainText(respuesta)

    def iniciar_anim_lista(self):
        self.lb_anim_lista.setMovie(self.movie)
        self.movie.start()

    def finalizar_anim_lista(self):
        self.lb_anim_lista.clear()
        self.movie.stop()

    def iniciar_anim_receta(self):
        self.lb_anim_receta.setMovie(self.movie)
        self.movie.start()

    def finalizar_anim_receta(self):
        self.lb_anim_receta.clear()
        self.movie.stop()

    def limpiar_campos(self):
        self.cb_ingredientes.setCurrentIndex(0)
        self.bt_gen_lista.setEnabled(False)
        self.lw_ingredientes.clear()
        self.bt_elim_ing.setEnabled(False)
        self.bt_gen_receta.setEnabled(False)
        self.lw_recetas.clear()
        self.te_receta.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    mw = VentanaPrincipal()
    widget = QtWidgets.QStackedWidget()
    widget.addWidget(mw)
    widget.setWindowTitle("Generador de recetas")
    widget.show()

    app.exec()