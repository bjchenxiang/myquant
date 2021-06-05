import os
import json

def read_setting(json_file):
    with open(json_file,'r') as f:
        return json.load(f)

def import_class(module_path,class_name):
    mdl = __import__(module_path,fromlist=[None])
    return getattr(mdl, class_name)