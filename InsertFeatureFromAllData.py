
import sys, os
import arcpy.mapping
import arcpy
from arcpy import env
import string

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
 
    return False

def get_value(sSource, sValueDefination, sSplit1, sSplit2):
    returnString = ""
    try:
        sDefPairs = sValueDefination.split(sSplit1)
        for sDefPair in sDefPairs:
            CurrentDef = sDefPair.split(sSplit2)
            if string.upper(CurrentDef[0].strip()) == string.upper(sSource):
                return CurrentDef[1].strip()
    except ValueError:
        pass
    return returnString

def ErrorHandler(sErrorMessage, filewriter):
    fw.write(sErrorMessage + "\n")
    fw.close()
    sys.exit()
    

env.overwriteOutput = True

# Define the jam values , template layer, Data source   

sValueDef = "-:-6; (X):-1;  **:-2;  ***:-3; *****:-5; N:-4"
workspace = "C:/Users/Baohong_Inno/Documents/Ji_Inno/Project/GIS_Desktop/Merge/Data/Data"
#workspace = "C:/Users/Baohong_Inno/Documents/Ji_Inno/Project/GIS_Desktop/Merge/Data/test2"
templateFeatures  = "C:/Users/Baohong_Inno/Documents/Ji_Inno/Project/GIS_Desktop/Merge/Result/Template.gdb/Result"
bDeleteRecordsForThisState = True

# generate the log file
fw = open("C:/Users/Baohong_Inno/Documents/Ji_Inno/Project/GIS_Desktop/Merge/log/logInsertDataAll" , 'w' )
if (fw == None):
    sys.exit("Cannot open file logInsertDataAll")

# Get the field type for the template layer
fieldListTemplate= arcpy.ListFields(templateFeatures)
sFieldNameTypeInTemplate = ""
for fieldTemplate in fieldListTemplate:
    if (string.upper(fieldTemplate.name) != "OBJECTID") and (string.upper(fieldTemplate.name) != "OBJECTID_1") and (string.upper(fieldTemplate.name) != "SHAPE") and (string.upper(fieldTemplate.name) != "SHAPE_LENGTH") and (string.upper(fieldTemplate.name) != "SHAPE_AREA"):
        if (fieldTemplate.name[:2] != "DP"):
            sFieldNameTypeInTemplate = sFieldNameTypeInTemplate + fieldTemplate.name + ":" + fieldTemplate.type + ";"
sFieldNameTypeInTemplate = sFieldNameTypeInTemplate[:-1]



for dirpath, dirnames, datatypes in arcpy.da.Walk(workspace,
                                                  datatype="FeatureClass",
                                                  type="Polygon"):
    for datatype in datatypes:
        sSourceLayerName = datatype.split("TRACT_")[1][3:]
        SourceFeatures = os.path.join(dirpath, datatype)


        # if desired, delete the previously loaded features for the same state
        if bDeleteRecordsForThisState:
            arcpy.MakeFeatureLayer_management(templateFeatures, "result_lyr")
            arcpy.SelectLayerByAttribute_management("result_lyr", "NEW_SELECTION", "\"STATE\" = '" + sSourceLayerName + "'")
            arcpy.DeleteFeatures_management("result_lyr")


        fieldListSource= arcpy.ListFields(SourceFeatures)

        # loop the source layer and insert the features into the template layer
        curTemplate = arcpy.InsertCursor(templateFeatures)
        featTemplate = curTemplate.newRow()
        fw.write("Start to insert feature from " + sSourceLayerName + "\n")
        fw.flush()
        os.fsync(fw)
        rowsSource = arcpy.UpdateCursor(SourceFeatures)

        rowNum = 1
        for rowSource in rowsSource:
            #fw.write("row number: " + str(rowNum) + "\n")
            polygon = rowSource.SHAPE
            featTemplate.shape = polygon
            featTemplate.setValue("STATE", sSourceLayerName)
            for fieldSource in fieldListSource:
                if (string.upper(fieldSource.name[:8]) != "OBJECTID") and (string.upper(fieldSource.name) != "SHAPE") and (string.upper(fieldSource.name) != "SHAPE_LENGTH") and (string.upper(fieldSource.name) != "SHAPE_AREA"):
                    if (fieldSource.name[:2] == "DP"):
                        #if not (fieldSource.name in MissingDPField): # do nothing if the DP_* field is missing in the template
                        if (sSourceLayerName == "PUERTO_RICO"):
                            fieldTemplateName = fieldSource.name.replace("PR", "")
                        else:
                            fieldTemplateName = fieldSource.name
                        
                        if (string.upper(fieldSource.type) != "STRING"):
                            if not rowSource.isNull(fieldSource.name):
                                try:
                                    featTemplate.setValue(fieldTemplateName, float(rowSource.getValue(fieldSource.name)))
                                except Exception as e:
                                    ErrorHandler("Error occurred at set value for field: " + fieldTemplateName + " at row: " + str(rowNum) + "  " + e.message, fw)
                        else: # then source DP field is of type text
                            if not rowSource.isNull(fieldSource.name):
                                sValue = rowSource.getValue(fieldSource.name)
                                if is_number(sValue):
                                    try:
                                        featTemplate.setValue(fieldTemplateName, float(sValue))
                                    except Exception as e:
                                        ErrorHandler("Error occurred at set value for field: " + fieldTemplateName + " at row: " + str(rowNum) + "  " + e.message, fw)
                                else:
                                    lastCharacter = sValue.strip()[-1]
                                    if (len(sValue.strip()) > 1) and ((lastCharacter == "+") or (lastCharacter == "-")):
                                        sStripComma = sValue.strip()[:-1].replace(",", "")
                                        if is_number(sStripComma):
                                            try:
                                                featTemplate.setValue(fieldTemplateName, float(sStripComma))
                                            except Exception as e:
                                                ErrorHandler("Error occurred at set value for field: " + fieldTemplateName + " at row: " + str(rowNum) + "  " + e.message, fw)
                                        else:
                                            ErrorHandler("The symbol  " + sValue + "  in field " + fieldTemplateName + " is not defined. Please check!", fw)
                                    else:
                                        desiredValue = get_value(sValue.strip(), sValueDef, ";", ":")
                                        if desiredValue == "":
                                            ErrorHandler("The symbol  " + sValue + "  in field " + fieldTemplateName + " is not defined. Please check!", fw)
                                        else:
                                            try:                                
                                                featTemplate.setValue(fieldTemplateName, float(desiredValue))
                                            except Exception as e:
                                                ErrorHandler("Error occurred at set value for field: " + fieldTemplateName + " at row: " + str(rowNum) + "  " + e.message, fw)
                                            
                    else: # the field is not DP_*
                        sFieldTypeInTemplate = get_value(fieldSource.name, sFieldNameTypeInTemplate, ";", ":")
                        if (sFieldTypeInTemplate != ""): 
                            if not rowSource.isNull(fieldSource.name):
                                if (string.upper(sFieldTypeInTemplate) == "STRING"):
                                    try:
                                        featTemplate.setValue(fieldSource.name, str(rowSource.getValue(fieldSource.name)))
                                    except Exception as e:
                                        ErrorHandler("Error occurred at set value for field: " + fieldSource.name + " at row: " + str(rowNum) + "  " + e.message, fw)
                                        
                                elif (string.upper(sFieldTypeInTemplate) == "DOUBLE"):
                                        try:
                                            featTemplate.setValue(fieldSource.name, float(rowSource.getValue(fieldSource.name)))
                                        except Exception as e:
                                            ErrorHandler("Error occurred at set value for field: " + fieldSource.name + " at row: " + str(rowNum) + "  " + e.message, fw)
                                elif (string.upper(sFieldTypeInTemplate) == "INTEGER"):
                                        try:
                                            featTemplate.setValue(fieldSource.name, int(rowSource.getValue(fieldSource.name)))
                                        except Exception as e:
                                            ErrorHandler("Error occurred at set value for field: " + fieldSource.name + " at row: " + str(rowNum) + "  " + e.message, fw)
                            
            curTemplate.insertRow(featTemplate)
            rowNum =  rowNum + 1
            
        del curTemplate


fw.close()


