import os,subprocess
from bson import ObjectId
from flask import Blueprint,request, send_file

from app.commons import errorCodes
from app.commons import buildResponse
from app.core.intentClassifier import IntentClassifier
from app.core import sequenceLabeler
from app.stories.models import Story

endpoint = Blueprint('api', __name__, url_prefix='/api')

# Request Handler
@endpoint.route('/v1', methods=['POST'])
def api():
    requestJson = request.get_json(silent=True)
    resultJson = requestJson
    print "DATA:",requestJson


    if requestJson:
        intentClassifier = IntentClassifier()
        storyId = intentClassifier.predict(requestJson.get("input"))

        story = Story.objects.get(id=ObjectId(storyId))
        if story.parameters:
            parameters = story.parameters
        else:
            parameters=[]

        if ((requestJson.get("complete") is None) or (requestJson.get("complete") is True)):



            resultJson["intent"] = {
                "name":story.intentName,
                "storyId":str(story.id)
            }

            if parameters:
                extractedParameters= sequenceLabeler.predict(storyId,
                                                             requestJson.get("input")
                                                             )
                missingParameters = []
                resultJson["missingParameters"] =[]
                resultJson["extractedParameters"] = {}
                resultJson["parameters"]=[]
                for parameter in parameters:
                    resultJson["parameters"].append({
                        "name": parameter.name,
                        "required": parameter.required
                    })

                    if parameter.required:
                        if parameter.name not in  extractedParameters.keys():
                            resultJson["missingParameters"].append(parameter.name)
                            missingParameters.append(parameter)

                resultJson["extractedParameters"] = extractedParameters
                if missingParameters:
                    resultJson["complete"] = False
                    currentNode = missingParameters[0]
                    resultJson["currentNode"] = currentNode["name"]
                    resultJson["speechResponse"] = currentNode["prompt"]
                else:
                    resultJson["complete"] = True
                    resultJson["speechResponse"] = story.speechResponse
            else:
                resultJson["complete"] = True
                resultJson["speechResponse"] = story.speechResponse

        elif (requestJson.get("complete") is False):
            if "cancel" not in story.intentName:
                storyId = requestJson["intent"]["storyId"]
                story = Story.objects.get(id=ObjectId(storyId))
                resultJson["extractedParameters"][requestJson.get("currentNode")] = requestJson.get("input")

                resultJson["missingParameters"].remove(requestJson.get("currentNode"))

                if len(resultJson["missingParameters"])==0:
                    resultJson["complete"] = True
                    resultJson["speechResponse"] = story.speechResponse
                else:
                    missingParameter = resultJson["missingParameters"][0]
                    resultJson["complete"] = False
                    currentNode = [node for node in story.parameters if missingParameter in node.name][0]
                    resultJson["currentNode"] = currentNode.name
                    resultJson["speechResponse"] = currentNode.prompt
            else:
                resultJson["currentNode"] = None
                resultJson["missingParameters"] = []
                resultJson["parameters"] = {}
                resultJson["intent"] = {}
                resultJson["complete"] = True
                resultJson["speechResponse"] = story.speechResponse
        try:
            extract_data=resultJson["extractedParameters"]
            if extract_data['url'] and extract_data['mail'] and extract_data['tag']:
             url=extract_data['url']
             mail_to=extract_data['mail']
             tag=extract_data['tag']
             # os.chdir('./AIspider')
             # print("PWD:",os.getcwd())
             # cmd=['scrapy crawl auto -a link='+str(url)+' -a mail_to='+str(mail_to)+'-a tag='+str(tag)]
             # with open('mylog.log', 'w') as logfile:
             #  pgm=[subprocess.Popen(c.split()) for c in cmd]
             # os.chdir("../")
        except:
            print"NO URL"
    else:
        resultJson = errorCodes.emptyInput
    print"RESULT:",resultJson
    return buildResponse.buildJson(resultJson)


# Text To Speech
@endpoint.route('/tts')
def tts():
    voices = {
              "american": "file://commons/fliteVoices/cmu_us_eey.flitevox"
              }
    os.system("echo \"" + request.args.get("text") + "\" | flite -voice " + voices["american"] + "  -o sound.wav")
    path_to_file = "../sound.wav"
    return send_file(
        path_to_file,
        mimetype="audio/wav",
        as_attachment=True,
        attachment_filename="sound.wav")

#Spider integration
def spider(url,mail_to):
    os.chdir('./AIspider')
    print("PWD:",os.getcwd())
    cmd=['scrapy crawl auto -a link='+str(url)+' -a mail_to='+str(mail_to)]
    with open('mylog.log', 'w') as logfile:
      pgm=[subprocess.Popen(c.split()) for c in cmd]
