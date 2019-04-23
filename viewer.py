#!/usr/bin/python3
# -*- coding: utf-8 -*-


import asyncio
import binascii

from bleak import discover
from bleak import BleakClient
from bleak import exc

import sys
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QWidget,
    QPushButton, QLineEdit, QCheckBox,
    QListWidget, QListWidgetItem,
    QTreeWidget, QTreeWidgetItem,
    QHBoxLayout, QVBoxLayout, QGroupBox,
    QApplication)

class Discover():

    def __init__(self):
        self.devices = []
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.run())
        self.client = None
        self.svcs = None
        self.char = None
    
    async def run(self):
        self.devices = await discover()
        for d in self.devices:
            print(d)

    def getServices(self, mac_addr):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.print_services(mac_addr, loop))

    async def print_services(self, mac_addr: str, loop: asyncio.AbstractEventLoop):
        async with BleakClient(mac_addr, loop=loop) as self.client:
            self.svcs = await self.client.get_services()
            '''
            for serviceKey, serviceValue in self.svcs.services.items():
                #print(serviceKey)
                #print(serviceValue)
                print(serviceValue.description)
                print(serviceValue.uuid)
                #print(serviceValue.characteristics)
                for characteristic in serviceValue.characteristics:
                    print(characteristic.uuid)
                    #print(characteristic.properties)
                    for property in characteristic.properties:
                        print(property)
            '''

    async def __readGattChar(self, mac_addr: str, uuid: str, loop: asyncio.AbstractEventLoop):
        x = await self.client.is_connected()
        print("Connected: {0}".format(x))
        if x:
            #await self.client.connect()
            self.char = await self.client.read_gatt_char(uuid)
            #await self.client.disconnect()

    def readGattChar(self, mac_addr, uuid):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__readGattChar(mac_addr, uuid, loop))
        return self.char

    async def __writeGattChar(self, mac_addr: str, uuid: str, data, loop: asyncio.AbstractEventLoop):
        x = await self.client.is_connected()
        print("Connected: {0}".format(x))
        if x:
            #await self.client.connect()
            self.char = await self.client.write_gatt_char(uuid, data)
            #await self.client.disconnect()

    def writeGattChar(self, mac_addr, uuid, data):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__writeGattChar(mac_addr, uuid, data, loop))

    async def __startNotify(self, mac_addr: str, uuid: str, callback, loop: asyncio.AbstractEventLoop):
        x = await self.client.is_connected()
        print("Connected: {0}".format(x))
        if x:
            #await self.client.connect()
            await self.client.start_notify(uuid, callback)
            #await self.client.disconnect()

    def startNotify(self, mac_addr, uuid, callback):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__startNotify(mac_addr, uuid, callback, loop))

class DiscoverUi(QWidget):
    
    def __init__(self):
        super().__init__()
        
        self.discover = Discover()
        self.devices = self.discover.devices
        self.listWidget = None
        self.treeWidget = None
        self.initUI()
        self.mac_addr = None

    def initDevices(self):
        for device in self.devices:
            newItem = QListWidgetItem()
            newItem.setText(device.name + " (" + device.address + ")")
            self.listWidget.addItem(newItem)

    def initUI(self):
        self.listWidget = QListWidget()
        self.initDevices()

        self.treeWidget = QTreeWidget()
        self.treeWidget.itemPressed.connect(self.onItemPressed)
        self.treeWidget.setColumnCount(4)
        self.treeWidget.setColumnWidth(0, 250)
        self.treeWidget.setColumnWidth(1, 300)
        self.treeWidget.setColumnWidth(2, 300)
        self.treeWidget.setColumnWidth(3, 150)
        self.treeWidget.setHeaderLabels(["Service", "Service UUID", "Characteristic UUID", "Characteristic Property"])

        btn = QPushButton("Read Services")
        btn.clicked.connect(self.onPushButton)

        groupDevices = QGroupBox("Devices")
        groupDevices.setMaximumWidth(300)

        vbox = QVBoxLayout()
        vbox.addWidget(self.listWidget)
        vbox.addWidget(btn)
        groupDevices.setLayout(vbox)

        self.btnR = QPushButton("Read")
        self.btnR.clicked.connect(self.onReadButton)
        self.btnW = QPushButton("Write")
        self.btnW.clicked.connect(self.onWriteButton)
        self.lneI = QLineEdit()
        self.chkN = QCheckBox("Notify")
        self.chkN.toggled.connect(self.onNotifyCheck)
        hbox = QHBoxLayout()
        hbox.addWidget(self.btnR)
        hbox.addWidget(self.btnW)
        hbox.addWidget(self.lneI)
        hbox.addWidget(self.chkN)

        groupProperty = QGroupBox("Property")
        #groupProperty.setLayout(vbox)
        groupProperty.setLayout(hbox)

        groupServices = QGroupBox("Services")

        vbox = QVBoxLayout()
        vbox.addWidget(self.treeWidget)
        vbox.addWidget(groupProperty)
        groupServices.setLayout(vbox)

        hbox = QHBoxLayout()
        hbox.addWidget(groupDevices)
        hbox.addWidget(groupServices)
        self.setLayout(hbox)
        
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle('BLE Discover')
        self.show()

    def onPushButton(self):
        try:
            self.mac_addr = self.devices[self.listWidget.currentRow()].address
            self.discover.getServices(self.mac_addr)
        except:
            print("Could not get GATT services.")
        else:
            svcs = self.discover.svcs
            for serviceKey, serviceValue in svcs.services.items():
                item = QTreeWidgetItem(None, [serviceValue.description, serviceValue.uuid])
                
                for characteristic in serviceValue.characteristics:
                    for property in characteristic.properties:
                        child = QTreeWidgetItem(["", "", characteristic.uuid, property])
                        item.addChild(child)

                self.treeWidget.addTopLevelItem(item)


    def onReadButton(self):
        byteArray = self.discover.readGattChar(self.mac_addr, self.chosenUuid)
        text = ''.join('{:02x}'.format(x) for x in byteArray)
        self.lneI.setText(text)

    def onWriteButton(self):
        text = self.lneI.text()
        print("onWriteButton")
        self.discover.writeGattChar(self.mac_addr, self.chosenUuid, bytes.fromhex(text))

    def notifyCallback(self, sender, data):
        text = ''.join('{:02x}'.format(x) for x in data)
        self.lneI.textChanged.emit(text)

    def onNotifyCheck(self, checked):
        if checked:
            print("onNotifyCheck")
            self.discover.startNotify(self.mac_addr, self.chosenUuid, self.notifyCallback)
        else:
            print("onNotifyCheck else")
            

    def onItemPressed(self, item, column):
        if item.child(0) is None:
            print(item)
            print(item.text(2))
            print(item.text(3))
            self.chosenUuid = item.text(2)
            property = item.text(3)

            if property == "read":
                self.btnR.setEnabled(True)
                self.btnW.setEnabled(False)
                self.lneI.setEnabled(False)
                self.chkN.setEnabled(False)
            elif property == "write":
                self.btnR.setEnabled(True)
                self.btnW.setEnabled(True)
                self.lneI.setEnabled(True)
                self.chkN.setEnabled(False)
            elif property == "notify":
                self.btnR.setEnabled(False)
                self.btnW.setEnabled(False)
                self.lneI.setEnabled(False)
                self.chkN.setEnabled(True)
                
        

if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = DiscoverUi()
    sys.exit(app.exec_())
