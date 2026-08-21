#!/usr/bin/env python3

import sys
import logging
import yaml
import xml.etree.ElementTree as ET
from . import dwlabObjectHandler



logger=logging.getLogger(__name__)

class dwlabSettings:
    def __init__(self, data=None):
        function_name = sys._getframe().f_code.co_name
        class_name=self.__class__.__name__
        function_name=class_name+"."+function_name
        logger.debug("Entering function "+str(function_name))

        if data is None:
            self._data = {}
        else:
            if isinstance(data,dict):
                self._data = data
            else:
                raise(" The passed data must be of type dict")

        logger.debug("Leaving function "+str(function_name))
        return

    @classmethod
    def read_yaml(cls, file_path):
        function_name = sys._getframe().f_code.co_name
        class_name=cls.__class__.__name__
        function_name=class_name+"."+function_name
        logger.debug("Entering function "+str(function_name))
        
        try:
            with open(file_path, 'r') as yaml_file:
                data = yaml.safe_load(yaml_file)
            logger.info(f"Data successfully loaded from {file_path}.")

        except Exception as e:
            logger.error(f"Error loading YAML data from {file_path}: {e}")
            raise e

        logger.debug("Leaving function "+str(function_name))
        return cls(data)

    @classmethod
    def read_xml(cls, file_path):
        function_name = sys._getframe().f_code.co_name
        class_name=cls.__class__.__name__
        function_name=class_name+"."+function_name
        logger.debug("Entering function "+str(function_name))

        tree = ET.parse(file_path)
        root = tree.getroot()
        data = cls._xml_to_dict_static(root)
        logger.info(f"Data successfully loaded from {file_path}.")
    
        logger.debug("Leaving function "+str(function_name))
        return cls(data)

    @staticmethod
    def _xml_to_dict_static(element):
        function_name = sys._getframe().f_code.co_name
        class_name="dwlabSettings"
        function_name=class_name+"."+function_name
        logger.debug("Entering function "+str(function_name))

        if len(element) > 0:
            result = {}
            for child in element:
                key = child.tag
                value = dwlabSettings._xml_to_dict_static(child)
                if key in result:
                    # Handle repeated tags as lists
                    if not isinstance(result[key], list):
                        result[key] = [result[key]]
                    result[key].append(value)
                else:
                    result[key] = value
            logger.debug("Leaving function "+str(function_name))
            return result
        else:
            logger.debug("Leaving function "+str(function_name))
            return element.text

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, new_data):
        function_name = sys._getframe().f_code.co_name
        class_name=self.__class__.__name__
        function_name=class_name+"."+function_name
        logger.debug("Entering function "+str(function_name))

        if isinstance(new_data, dict):
            self._data = new_data
        else:
            raise ValueError("Data must be a dictionary.")
        logger.debug("Leaving function "+str(function_name))
        return

    def write_yaml(self, file_path):
        function_name = sys._getframe().f_code.co_name
        class_name=self.__class__.__name__
        function_name=class_name+"."+function_name
        logger.debug("Entering function "+str(function_name))

        with open(file_path, 'w') as yaml_file:
            yaml.dump(self.data, yaml_file, default_flow_style=False)
        logger.info(f"Data successfully written to {file_path} as YAML.")

        logger.debug("Leaving function "+str(function_name))
        return
    
    def write_xml(self, file_path):
        function_name = sys._getframe().f_code.co_name
        class_name=self.__class__.__name__
        function_name=class_name+"."+function_name
        logger.debug("Entering function "+str(function_name))

        root = self._dict_to_xml("root", self.data)
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding="utf-8", xml_declaration=True)
        logger.info(f"Data successfully written to {file_path} as XML.")

        logger.debug("Leaving function "+str(function_name))
        return
    
    def _dict_to_xml(self, tag, data):
        function_name = sys._getframe().f_code.co_name
        class_name=self.__class__.__name__
        function_name=class_name+"."+function_name
        logger.debug("Entering function "+str(function_name))

        element = ET.Element(tag)
        if isinstance(data, dict):
            for key, value in data.items():
                child = self._dict_to_xml(key, value)
                element.append(child)
        elif isinstance(data, list):
            for item in data:
                child = self._dict_to_xml("item", item)
                element.append(child)
        else:
            element.text = str(data)

        logger.debug("Leaving function "+str(function_name))
        return element

    def _xml_to_dict(self, element):
        function_name = sys._getframe().f_code.co_name
        class_name=self.__class__.__name__
        function_name=class_name+"."+function_name
        logger.debug("Entering function "+str(function_name))

        if len(element) > 0:
            result = {}
            for child in element:
                key = child.tag
                value = self._xml_to_dict(child)
                if key in result:
                    # Handle repeated tags as lists
                    if not isinstance(result[key], list):
                        result[key] = [result[key]]
                    result[key].append(value)
                else:
                    result[key] = value
            logger.debug("Leaving function "+str(function_name))
            return result
        else:
            logger.debug("Leaving function "+str(function_name))
            return element.text

    def get_variable(self,variableName):
        function_name = sys._getframe().f_code.co_name
        class_name=self.__class__.__name__
        function_name=class_name+"."+function_name
        logger.debug("Entering function "+str(function_name))

        logger.debug("variableName="+str(variableName))
        
        object=dwlabObjectHandler.dictToObject(self.data)
        if hasattr(object, variableName):
            logger.debug("variableName "+str(variableName)+" exists")
            variable=getattr(object, variableName)
        else:
            logger.debug("variableName "+str(variableName)+" noes not exists")
            variable=""

        logger.debug("Leaving function "+str(function_name))
        return variable

    def put_variable(self, variableName, variableValue):
        function_name = sys._getframe().f_code.co_name
        class_name=self.__class__.__name__
        function_name=class_name+"."+function_name
        logger.debug("Entering function "+str(function_name))

        logger.debug(f"Adding/Updating variable '{variableName}' with value: {variableValue}")

        if not isinstance(variableName, str):
            logger.error("Variable name must be a string.")
            raise ValueError("Variable name must be a string.")

        self._data[variableName] = variableValue

        logger.debug("Variable added/updated successfully.")

        logger.debug("Leaving function "+str(function_name))
        return
    
    def to_dict(self):
        function_name = sys._getframe().f_code.co_name
        class_name=self.__class__.__name__
        function_name=class_name+"."+function_name
        logger.debug("Entering function "+str(function_name))
        
        if isinstance(self._data, dict):
            data=self._data
        else:
            data=self._data.to_dict()

        logger.debug("Leaving function "+str(function_name))
        return data
