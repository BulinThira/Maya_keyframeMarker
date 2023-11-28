# randomMaterial.py - Python Script

# DESCRIPTION: Tool for marking animation keyframe
# REQUIRE: Python2 - Python3
# AUTHOR: BulinThira - Github

"""
#run the script below in Maya Script Editor after putting the .py file in the Maya scripts folder

from importlib import reload
import keyframeMarker
reload(keyframeMarker)
example = keyframeMarker.docking(keyframeMarker.MainWidget)
"""

from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from shiboken2 import wrapInstance
from importlib import reload
import maya.OpenMayaUI as omui
import maya.cmds as cmds
import ast

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#! define maya ui pointer
maya_ptr = omui.MQtUtil.mainWindow()
ptr = wrapInstance(int(maya_ptr), QWidget)

class MainWidget(QWidget):
    """
    main widget that contains TableWidget
    """
    def __init__(self, *args, **kwargs):
        super(MainWidget, self).__init__(*args, **kwargs)

        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowTitle("Keyframe Marker")

        self.edit_frame_dialog = EditInfo()

        self.horizontal_spacer = QSpacerItem(20, 40, QSizePolicy.Expanding)

        self.favourite_item_dict = {"frame":[], "objects":[]}

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("add")
        self.add_button.setMinimumWidth(200)
        self.add_button.clicked.connect(self.add_favourite)
        self.clear_button = QPushButton("remove")
        self.clear_button.setMinimumWidth(200)
        self.clear_button.clicked.connect(self.clear_favourite)
        self.buttons_layout.addWidget(self.add_button)
        self.buttons_layout.addWidget(self.clear_button)
        self.buttons_layout.addItem(self.horizontal_spacer)

        header = ["frame", "objects"]
        self.main_table = QTableWidget(len(header), 0)
        self.main_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for index, item in enumerate(header):
            self.main_table.setVerticalHeaderItem(index, QTableWidgetItem(item))
        self.main_table.setColumnWidth(3, 90)

        self.main_table.selectionModel().selectionChanged.connect(self.on_selectionChanged)

        self.main_layout.addLayout(self.buttons_layout)
        self.main_layout.addWidget(self.main_table)
    
    def add_favourite(self):
        """
        add item to the TableWidget
        """
        columnPosition = self.main_table.columnCount()
        self.main_table.insertColumn(columnPosition)

        frame = cmds.currentTime(query=True)
        obj = object_query_command()

        if obj is not None:
            if len(obj) == 1:
                obj = (obj[0])
            else:
                obj = str(obj)
        else:
            obj = ""
            logger.warning("No object has been added. RMB on the cell for Edit Info")

        frame_item = FavouriteItem(str(frame))
        object_item = FavouriteItem(obj)

        self.main_table.setItem(0 , columnPosition, frame_item)
        self.main_table.setItem(1 , columnPosition, object_item)

        self.favourite_item_dict["frame"].append(frame_item.item_name())
        self.favourite_item_dict["objects"].append(object_item.item_name())
    
    def on_selectionChanged(self, selected):
        """
        PyQt method: activated when the TableWidget's cell is left-clicked
        select objects and Keyframe written in the TableWidget's cell
        """
        for ix in selected.indexes():
            obj_member_list = (self.main_table.item(1, ix.column()).item_name())
            if obj_member_list != "":
                if obj_member_list.startswith("["):
                    obj_member_list = ast.literal_eval(obj_member_list)
                # cmds.currentTime(float(self.main_table.item(0, ix.column()).item_name()))
                cmds.select(clear=True)
                cmds.select(obj_member_list, add=True)
            else:
                cmds.select(clear=True)
            cmds.currentTime(float(self.main_table.item(0, ix.column()).item_name()))
    
    def contextMenuEvent(self, event):
        """
        PyQt method: activated when the TableWidget's cell is right-clicked
        popup the menu
        """
        selected_column = self.main_table.selectedItems()[0].column()
        self.menu = QMenu(self)
        edit_action = QAction('Edit Info', self)
        edit_action.triggered.connect(self.edit_info_command)

        if self.is_text_color_red(column=selected_column):
            mark_action = QAction('Unmark Info', self)
            mark_action.triggered.connect(
                lambda: self.mark_command(selected_column, 200, 200, 200)
                )
        else:
            mark_action = QAction('Mark Info', self)
            mark_action.triggered.connect(
                lambda: self.mark_command(selected_column, 255, 0, 0)
                )
        self.menu.addAction(edit_action)
        self.menu.addAction(mark_action)
        if len(self.main_table.selectedItems()) > 0:
            self.menu.popup(QCursor.pos())
    
    def mark_command(self, column=0, r=0, g=0, b=0):
        """
        mainly set color of Keyframe text (red for marked and grey-white for unmarked)
        and then clear selection of the 
        
        Args:
            column (int): column of the selected frame and objects
            r (int): red color value
            g (int): green color value
            b (int): blue color value
        """
        self.main_table.item(0, column).setForeground(QColor(r, g, b))
        self.main_table.clearSelection()
    
    def edit_info_command(self):
        """
        main function of editing info (frame and objects)
        """
        selected_item_column = self.main_table.selectedItems()[0].column()
        selected_item = self.main_table.item(0, selected_item_column)
        self.edit_frame_dialog.get_latest_frame(
            float(selected_item.item_name())
            )
        self.edit_frame_dialog.bake_objects_name(
            self.main_table.item(1, selected_item.column()).item_name()
        )
        self.edit_frame_dialog.show()

        result = self.edit_frame_dialog.exec_()

        if result == QDialog.Accepted:
            self.main_table.item(0, selected_item.column()).update_item(
                self.edit_frame_dialog.ret_info(0)
            )
            self.main_table.item(1, selected_item.column()).update_item(
                self.edit_frame_dialog.ret_info(1)
            )
            self.edit_frame_dialog.objects_item_list.clear_item()

    def clear_favourite(self, selected):
        """
        remove whole items from TableWidget
        """
        unique_columns = set()
        selected_items = self.main_table.selectedItems()
        if selected_items != []:
            for item in selected_items:
                item_column = item.column()
                unique_columns.add(item_column)
            for _item in reversed(list(unique_columns)):
                self.main_table.removeColumn(_item)
        else:
            logger.error("No cell has been selected.")
            return
    
    def is_text_color_red(self, column):
        """
        check if text color is red QColor(25, 0, 0)

        Args:
            column (int): selected column
        
        Returns:
            bool: if the color is red
        """
        color = self.main_table.item(0, column).foreground().color()
        return color == QColor(255, 0, 0)


class FavouriteItem(QTableWidgetItem):
    def __init__(self, item):
        """
        specifically create item of main TableWidget

        Args:
            item (str): item from TableWidget
        """
        super(FavouriteItem, self).__init__()
        self.info_item = item
        self.display_item = item

        if (self.info_item).startswith("["):
            item_list = ast.literal_eval(item)
            self.display_item = "..{add}".format(add=item_list[0])

        self.setText(self.display_item)
        self.setTextAlignment(Qt.AlignCenter)
    
    def item_name(self):
        """
        function for returnnig obj name

        Returns:
            str: name of obj
        """
        return(self.info_item)
    
    def update_item(self, new_item=""):
        """
        change data and set new item display name
        """
        old_info = self.info_item
        if new_item.startswith("["):
            item_list = ast.literal_eval(new_item)
            if len(item_list) > 1:
                self.info_item = new_item
                self.display_item = "..{add}".format(add=item_list[0])
            else:
                self.info_item = str(new_item[0])
                self.display_item = self.info_item
        else:
            self.info_item = new_item
            self.display_item = self.info_item
        self.setText(self.display_item)
        # print("change to: ", self.display_item, " from ", old_info)
    
    def display_item_name(self):
        """
        function for returnning display name

        Returns:
            str: display name
        """
        return(self.display_item)


class EditInfo(QDialog):
    def __init__(self, parent=ptr):
        """
        create edit info Qdialog

        Args:
            parent (pointer): maya ui pointer (defined on the of this script)
        """
        super(EditInfo, self).__init__(parent)
        self.setFixedSize(QSize(300,200))
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.setWindowTitle("Edit Frame Info")

        self.objects_item_list = ObjectListWidget()

        self.info_grid_layout = QGridLayout()
        self.button_layout = QHBoxLayout()
        self.label = QLabel("Keyframe:")
        self.get_current_button = QPushButton("select")
        self.get_current_button.setMinimumHeight(20)
        self.get_current_button.clicked.connect(
            lambda: self.get_latest_frame(frame_value=cmds.currentTime(query=True))
            )
        self.spinbox = QDoubleSpinBox()
        #todo set value of the spinbox as current duration
        self.spinbox.setDecimals(1)
        self.spinbox.setValue(1.0)
        self.spinbox.setMaximum(100000.0)

        self.second_label = QLabel("Objects:")
        self.add_button = QPushButton("add")
        self.add_button.setMinimumHeight(20)
        self.add_button.clicked.connect(self.objects_item_list.add_new_item)
        self.clear_button = QPushButton("remove")
        self.clear_button.setMinimumHeight(20)
        self.clear_button.clicked.connect(self.objects_item_list.delete_current_index)

        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.setCenterButtons(True)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.info_grid_layout.addWidget(self.label, 0, 0)
        self.info_grid_layout.addWidget(self.spinbox, 0, 1)
        self.info_grid_layout.addWidget(self.get_current_button, 0, 2)
        self.info_grid_layout.addWidget(self.second_label, 1, 0)
        self.info_grid_layout.addWidget(self.add_button, 1, 1)
        self.info_grid_layout.addWidget(self.clear_button, 1, 2)

        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)

        self.main_layout.addLayout(self.info_grid_layout)
        self.main_layout.addWidget(self.objects_item_list)
        self.main_layout.addWidget(self.button_box)
    
    def get_latest_frame(self, frame_value=0.0):
        """
        set keyframe value to the double spinbox

        Args:
            frame_value (float): keyframe value
        """
        self.spinbox.setValue(frame_value)
    
    def bake_objects_name(self, obj=""):
        """
        bake objects (from TableWidget) to the ListWidget

        Args:
            obj (str): referred objects
        """
        obj_list = []
        if obj != "":
            if obj.startswith("["):
                obj_list = ast.literal_eval(obj)
            else:
                obj_list.append(obj)
            for member in obj_list:
                self.objects_item_list.get_obj_name(member)
    
    def ret_info(self, info_order=0):
        """
        return data from ListWidget

        Args:
            info_order (int): frame value (0) or objects vlaue (1)
        
        Returns:
            str: text (that will be used to replace the old one in TableWidget)
        """
        if info_order == 0:
            ret = str(self.spinbox.value())
        elif info_order == 1:
            original_list = self.objects_item_list.return_item_list()
            if len(original_list) == 1:
                object_name = original_list[0]
                ret = str(object_name)
            else:
                ret = str(original_list)
        return(ret)
    
    def closeEvent(self, event):
        """
        PyQt method: activated when the TableWidget's cell is closed
        """
        self.objects_item_list.clear_item()
        event.accept()


class ObjectListWidget(QListWidget):
    """
    interactive ListWidget for showing main controller's children
    """
    def __init__(self, *args, **kwargs):
        super(ObjectListWidget, self).__init__(*args, **kwargs)
        self.item_list = []
    
    def get_obj_name(self, obj_name="None"):
        """
        add stuff from the TableWidget into ListWidget

        Args:
            obj_name (str): object's name
        """
        item = ObjectListWidgetItem(obj_name)
        self.indexFromItem(item)
        self.addItem(item)
        self.item_list.append(item.item_name())
    
    def add_new_item(self):
        """
        add new selected objects in Maya viewport into ListWidget
        """
        objs_name = object_query_command()
        for member in objs_name:
            item = ObjectListWidgetItem(member)
            self.indexFromItem(item)

            self.addItem(item)
            self.item_list.append(member)
    
    def delete_current_index(self):
        """
        delete selected item in ListWidget
        """
        current_item = self.selectedItems()
        self.item_list.remove(current_item[0].item_name())
        self.takeItem(self.currentRow())
    
    def return_item_list(self):
        """
        return item list

        Returns:
            list: list of every item
        """
        return(self.item_list)
    
    def clear_item(self):
        """
        clear both display item and inner item list of this ListWidget
        """
        self.clear()
        self.item_list.clear()


class ObjectListWidgetItem(QListWidgetItem):
    """
    create single item of ObjectListWidget

    Args:
        obj_item (str): name of obj item
    """
    def __init__(self, obj_item):
        super(ObjectListWidgetItem, self).__init__()
        self.obj_item = obj_item
        self.setText(self.obj_item)
    
    def item_name(self):
        """
        function for returnnig child node

        Returns:
            str: name of child node
        """
        return(self.obj_item)


def object_query_command(quantity=""):
    """
    function that returns selected
    this function can returns various type of variable depends on input argument

    Args:
        quantity (str): default for type of return; single means one object's name will be returned

    Returns:
        None: if nothing is selected
        str: if input argument is defined as single (return the first member of list)
        list: return all of selections
    """
    object_name_list = cmds.ls(selection=True)
    if len(object_name_list) == 0:
        return
    if quantity == "single":
        return(object_name_list[0])
    else:
        # if len(object_name_list) == 1:
        #     return(object_name_list[0])
        # else:
        return(object_name_list)

def docking(working_widget, width=100, show=True):
    """
    docking `working_widget` into Maya UI
    originally dock beside Range Slider (Maya Classic & Animation)

    Args:
        working_widget (QWidget): Class
        width (int): width of the docked widget
        show (bool, optional): show the resulting dock
    """

    main_window = MainWidget()
    name = working_widget.__name__
    label = main_window.windowTitle()

    try:
        cmds.deleteUI(name)
    except RuntimeError:
        pass

    dockControl = cmds.workspaceControl(
        name,
        tabToControl=["RangeSlider", -1],
        initialWidth=width,
        resizeWidth=width,
        minimumHeight=155,
        minimumWidth=500,
        label=label,
    )

    dockPtr = omui.MQtUtil.findControl(dockControl)
    dockWidget = wrapInstance(int(dockPtr), QWidget)

    dockWidget.setAttribute(Qt.WA_DeleteOnClose)
    child = working_widget(dockWidget)
    dockWidget.layout().addWidget(child)

    if show:
        cmds.evalDeferred(
            lambda *args: cmds.workspaceControl(
                dockControl,
                edit=True,
                resizeHeight=155,
                resizeWidth=100,
                restore=True
            )
        )

    return child
