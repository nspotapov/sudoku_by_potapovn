from PyQt5.QtCore import QTimer
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget, QMessageBox, QInputDialog, QLineEdit

from sudoku_database_cursor import SudokuDatabaseCursor

from settings import GAME_TIMER_SECOND
from settings import SHOW_SUDOKU_SOLVED_MATRIX
from settings import COLOR_OF_SUDOKU_DYNAMIC_CELLS
from settings import COLOR_OF_SUDOKU_CONSTANT_CELLS

from settings import ICON_PATH
from settings import DEBUG_MODE

IN_GAME = 0
PAUSE = 1
SOLVED = 2
SAVED = 3


class GameWindowUiForm(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(498, 499)

        Form.setWindowIcon(QtGui.QIcon(ICON_PATH))

        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btn_back = QtWidgets.QPushButton(Form)
        self.btn_back.setMinimumSize(QtCore.QSize(0, 10))
        self.btn_back.setObjectName("btn_back")
        self.horizontalLayout.addWidget(self.btn_back)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)

        self.btn_hard_win = QtWidgets.QPushButton(Form)
        self.btn_hard_win.setMinimumSize(QtCore.QSize(0, 10))
        self.btn_hard_win.setObjectName("btn_hard_win")
        self.horizontalLayout.addWidget(self.btn_hard_win)
        self.btn_hard_win.hide()

        self.btn_game_timer = QtWidgets.QPushButton(Form)
        self.btn_game_timer.setMinimumSize(QtCore.QSize(0, 10))
        self.btn_game_timer.setObjectName("btn_game_timer")
        self.horizontalLayout.addWidget(self.btn_game_timer)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.sudoku_layout = QtWidgets.QGridLayout()
        self.sudoku_layout.setObjectName("sudoku_layout")
        self.verticalLayout.addLayout(self.sudoku_layout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Судоку"))
        self.btn_back.setText(_translate("Form", "В главное меню"))
        self.btn_game_timer.setText(_translate("Form", ""))
        self.btn_hard_win.setText(_translate("Form", "Выиграть"))


class GameWindow(GameWindowUiForm, QWidget):
    """
    Класс окна игры
    """
    def __init__(self, parent_window, sudoku):
        super(GameWindowUiForm, self).__init__()
        self.sudoku = sudoku
        self.parent_window = parent_window
        self.child_window = None
        self.setupUi(self)

        if SHOW_SUDOKU_SOLVED_MATRIX:
            sudoku.show_solved_matrix()

        if DEBUG_MODE:
            self.btn_hard_win.show()
            self.btn_hard_win.clicked.connect(self.btn_hard_win_clicked)

        current_sudoku_matrix = sudoku.get_current_sudoku_state()
        if current_sudoku_matrix is None:
            current_sudoku_matrix = sudoku.get_problem_matrix()
        self.current_sudoku_state = current_sudoku_matrix
        self.sudoku_size = sudoku.get_size()
        self.initialize_sudoku_interface()
        self.update_sudoku_interface()

        self.db_cursor = None
        self.game_status = IN_GAME

        game_time = sudoku.get_game_time()
        if game_time is None:
            game_time = 0
        self.game_time = game_time
        self.game_timer = QTimer()
        self.game_timer.start(GAME_TIMER_SECOND)
        self.game_timer.timeout.connect(self.timer_tick)

        # Кнопка с таймером
        # При нажатии останавливает время и скрывает судоку
        self.btn_game_timer.clicked.connect(self.btn_game_timer_clicked)

        self.update_game_time()

        # Подключаем кнопку "В главное меню"
        self.btn_back.clicked.connect(self.btn_back_clicked)

    def btn_back_clicked(self):
        """
        Срабатывает по нажатию кнопки "Назад"
        """
        self.close()

    def save_game(self):
        """
        Сохраняет игру
        """
        if self.db_cursor is None:
            self.db_cursor = SudokuDatabaseCursor()
        self.sudoku.set_current_sudoku_state(self.current_sudoku_state)
        self.sudoku.set_game_time(self.game_time)
        self.db_cursor.add_game_save(self.sudoku)

    def save_record(self):
        """
        Сохраняет рекорд
        """
        if self.db_cursor is None:
            self.db_cursor = SudokuDatabaseCursor()

        player_name, ok_pressed = QInputDialog.getText(self, 'Судоку решено!',
                                                       'Введите свое имя:',
                                                       QLineEdit.Normal,
                                                       'UnknownPlayer')
        if ok_pressed:
            self.sudoku.set_game_time(self.game_time)
            self.db_cursor.add_game_record(self.sudoku, player_name)
            return True

        return False

    def save_game_question_message_box(self):
        """
        Показывает диалог сохранения игры
        """
        self.game_status = PAUSE
        messagebox = QMessageBox()

        messagebox.setWindowIcon(QtGui.QIcon(ICON_PATH))

        messagebox.setIcon(QMessageBox.Information)
        messagebox.setWindowTitle('Выход')
        messagebox.setText('Сохранить игру перед выходом?')
        btn_exit_with_save = messagebox.addButton('Сохранить и выйти', QMessageBox.AcceptRole)
        btn_exit_without_save = messagebox.addButton('Выйти без сохранения',
                                                     QMessageBox.ActionRole)
        btn_exit_cancelled = messagebox.addButton('Отмена', QMessageBox.RejectRole)
        messagebox.exec()
        clicked_button = messagebox.clickedButton()
        if clicked_button == btn_exit_with_save:
            self.save_game()
            return True
        elif clicked_button == btn_exit_without_save:
            return False
        elif clicked_button == btn_exit_cancelled:
            self.game_status = IN_GAME
            return None

    def save_record_question_message_box(self):
        """
        Показывает диалог сохранения рекрода
        """
        messagebox = QMessageBox()

        messagebox.setWindowIcon(QtGui.QIcon(ICON_PATH))

        messagebox.setIcon(QMessageBox.Information)
        messagebox.setWindowTitle('Выход')
        messagebox.setText('Сохранить рекорд перед выходом?')
        btn_exit_with_save = messagebox.addButton('Сохранить и выйти', QMessageBox.AcceptRole)
        btn_exit_without_save = messagebox.addButton('Выйти без сохранения',
                                                     QMessageBox.ActionRole)
        btn_exit_cancelled = messagebox.addButton('Отмена', QMessageBox.RejectRole)
        messagebox.exec()
        clicked_button = messagebox.clickedButton()

        if clicked_button == btn_exit_with_save:
            if self.save_record():
                return True
            return None

        elif clicked_button == btn_exit_without_save:
            return False

        elif clicked_button == btn_exit_cancelled:
            return None

    def timer_tick(self):
        """
        Инкрементирует игровой таймер
        """
        if self.game_status == IN_GAME:
            self.game_time += 1
            self.update_game_time()

    def update_game_time(self):
        """
        Обновляет игровое время в окне
        """
        seconds = self.game_time
        minutes = seconds // 60
        hours = minutes // 60
        seconds = seconds % 60
        minutes = minutes % 60

        if hours:
            hours = str(hours).rjust(2, '0') + ':'
        else:
            hours = ''
        minutes = str(minutes).rjust(2, '0') + ':'
        seconds = str(seconds).rjust(2, '0')

        timer = hours + minutes + seconds
        self.btn_game_timer.setText(timer.strip())

    def btn_game_timer_clicked(self):
        """
        Срабатывает при нажатии на таймер:
            устанавливает паузу и продолжает игру
        """
        if self.game_status == IN_GAME:
            self.game_status = PAUSE
            self.cover_sudoku(True)
        elif self.game_status == PAUSE:
            self.game_status = IN_GAME
            self.cover_sudoku(False)

    def cover_sudoku(self, covered):
        """
        Скрывает или показывает судоку
        """
        for i in range(self.sudoku_size ** 2):
            for j in range(self.sudoku_size ** 2):
                if covered:
                    getattr(self, f'btn_{i}_{j}').setDisabled(True)
                    getattr(self, f'btn_{i}_{j}').setText(' ')
                    getattr(self, f'btn_{i}_{j}'). \
                        setStyleSheet(
                        "QPushButton {"
                        "background-color: rgb(225, 225, 225);"
                        "color: rgb(225, 225, 225);"
                    )

                else:
                    problem_sudoku = self.sudoku.get_problem_matrix()
                    value = self.current_sudoku_state[i][j]
                    getattr(self, f'btn_{i}_{j}').setDisabled(False)
                    getattr(self, f'btn_{i}_{j}').setText(str(value) if value else ' ')
                    if problem_sudoku[i][j] != 0:
                        getattr(self, f'btn_{i}_{j}'). \
                            setStyleSheet("QPushButton {"
                                          "background-color: rgb(255, 255, 255);"
                                          "color: #000000;"
                                          "border: 1px solid;}"
                                          )
                    else:
                        getattr(self, f'btn_{i}_{j}').setStyleSheet(
                            "background-color: rgb(255, 255, 255);"
                            "color: #4a90e2;"
                            "border: 1px solid;"
                        )

    def disable_sudoku(self):
        """
        Устанавливает нужный цвет неактивных ячеек
        """
        for i in range(self.sudoku_size ** 2):
            for j in range(self.sudoku_size ** 2):
                getattr(self, f'btn_{i}_{j}').setDisabled(True)
                getattr(self, f'btn_{i}_{j}').setStyleSheet("background-color: rgb(225, 225, 225);")

    def initialize_sudoku_interface(self):
        """
        Инициализирует новую игру
        """
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        for i in range(self.sudoku_size):
            for j in range(self.sudoku_size):
                name = 'layout%i%d' % (i, j)
                setattr(self, name, QtWidgets.QGridLayout())
                getattr(self, name).setHorizontalSpacing(0)
                getattr(self, name).setVerticalSpacing(0)
                self.sudoku_layout.addLayout(getattr(self, name), i, j)

        problem_matrix = self.sudoku.get_problem_matrix()

        for i in range(self.sudoku_size ** 2):
            for j in range(self.sudoku_size ** 2):
                name = f'layout{i // self.sudoku_size}{j // self.sudoku_size}'
                setattr(self, f'btn_{i}_{j}', QtWidgets.QPushButton())
                getattr(self, name).addWidget(getattr(self, f'btn_{i}_{j}'),
                                              i % self.sudoku_size,
                                              j % self.sudoku_size, 1, 1)
                getattr(self, f'btn_{i}_{j}').setSizePolicy(sizePolicy)
                getattr(self, f'btn_{i}_{j}').setMinimumSize(QtCore.QSize(30, 30))

                my_font = QtGui.QFont()
                my_font.setPixelSize(20)
                getattr(self, f'btn_{i}_{j}').setFont(my_font)
                getattr(self, f'btn_{i}_{j}').setObjectName(f'btn_{i}_{j}')

                if problem_matrix[i][j] != 0:
                    getattr(self, f'btn_{i}_{j}'). \
                        setStyleSheet("QPushButton {"
                                      "background-color: rgb(255, 255, 255);"
                                      f"color: {COLOR_OF_SUDOKU_CONSTANT_CELLS};"
                                      "border: 1px solid;}"
                                      )
                else:
                    getattr(self, f'btn_{i}_{j}').setStyleSheet(
                        "background-color: rgb(255, 255, 255);"
                        f"color: {COLOR_OF_SUDOKU_DYNAMIC_CELLS};"
                        "border: 1px solid;"
                    )

                getattr(self, f'btn_{i}_{j}').clicked.connect(self.sudoku_btn_clicked)

    def sudoku_btn_clicked(self):
        """
        Срабатывает при нажатии на кнопку игрового поля
        """
        button = self.sender()
        row, col = list(map(int, button.objectName().split('_')[-2:]))
        if self.sudoku.get_problem_matrix()[row][col] == 0:
            value = self.current_sudoku_state[row][col]
            value = (value + 1) % (self.sudoku_size ** 2 + 1)
            self.current_sudoku_state[row][col] = value
            button.setText(str(value) if value else ' ')
            if self.check_win():
                self.game_status = SOLVED
                self.disable_sudoku()
                self.save_record()

    def update_sudoku_interface(self):
        """
        Обновляет состояние и значение всех кнопок игрового поля
        """
        for i, row in enumerate(self.current_sudoku_state):
            for j, value in enumerate(row):
                getattr(self, f'btn_{i}_{j}').setText(str(value) if value else ' ')

    def check_win(self):
        """
        Проверяет судоку на решенность
        """
        return self.current_sudoku_state == self.sudoku.get_solved_matrix()

    def btn_hard_win_clicked(self):
        """
        Выигрывает текущую игру (DEBUG MODE)
        """
        self.game_status = SOLVED
        self.disable_sudoku()
        if self.save_record():
            self.game_status = SAVED
            self.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Вызывает необходимые диалоги сохранения
        Срабатывает при закрытии окна
        """
        result = None

        if self.game_status == SOLVED:
            result = self.save_record_question_message_box()
        elif self.game_status == IN_GAME:
            result = self.save_game_question_message_box()
        elif self.game_status == SAVED:
            result = True

        if result is not None:
            self.parent_window.show()
            event.accept()
        else:
            event.ignore()
