from tools import lang
from tools import tag_parser

def user(cmd:str):
    parsed = tag_parser.parse_all(cmd)
    if parsed['matches'] == []:
        return {
                    "role":"user",
                    "content": cmd
                }
    else:
        content = []
        for i in parsed['matches']:
            if i['tag'] == 'image':
                content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{i['data']}"
                            }
                        })
            elif i['tag'] == 'imageurl':
                content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": i['data']
                            }
                        })
            elif i['tag'] == 'audio':
                content.append({
                            "type": "input_audio",
                            "input_audio": {
                                "data": f"data:audio/wav;base64,{i['data']}"
                            }
                        })
            elif i['tag'] == 'audiourl':
                content.append({
                            "type": "input_audio",
                            "input_audio": {
                                "data": i['data']
                            }
                        })
            elif i['tag'] == 'video':
                content.append({
                            "type": "video_url",
                            "video_url": {
                                "url": f"data:video/mp4;base64,{i['data']}"
                            },
                            "fps": 2,
                            "media_resolution": "default"
                        })
            elif i['tag'] == 'videourl':
                content.append({
                            "type": "video_url",
                            "video_url": {
                                "url": i['data']
                            },
                            "fps": 2,
                            "media_resolution": "default"
                        })
            else:
                pass
        content.append({
                            "type": "text",
                            "text": parsed['rest']
                        })
        return {
                    "role":"user",
                    "content": content
                }