from tools import lang
def user(cmd:str):
    if '<tool_call>image</tool_call>' in cmd:
        return {
                    "role":"user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{cmd.split('<tool_call>image</tool_call>')[1].split('\n')[0]}"
                            }
                        },
                        {
                            "type": "text",
                            "text": lang.lang['bot.multimodel.imread']
                        }
                    ]
                }
    elif '<tool_call>imageurl</tool_call>' in cmd:
        return {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": cmd.split('<tool_call>imageurl</tool_call>')[1].split('\n')[0]
                            }
                        },
                        {
                            "type": "text",
                            "text": lang.lang['bot.multimodel.imread']
                        }
                    ]
                }
    elif '<tool_call>audio</tool_call>' in cmd:
        return {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": f"data:audio/wav;base64,{cmd.split('<tool_call>audio</tool_call>')[1].split('\n')[0]}"
                            }
                        },
                        {
                            "type": "text",
                            "text": lang.lang['bot.multimodel.auread']
                        }
                    ]
                }
    elif '<tool_call>audiourl</tool_call>' in cmd:
        return {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": cmd.split('<tool_call>audiourl</tool_call>')[1].split('\n')[0]
                            }
                        },
                        {
                            "type": "text",
                            "text": lang.lang['bot.multimodel.auread']
                        }
                    ]
                }
    elif '<tool_call>video</tool_call>' in cmd:
        return {
                    "role": "user",
                    "content": [
                        {
                            "type": "video_url",
                            "video_url": {
                                "url": f"data:video/mp4;base64,{cmd.split('<tool_call>video</tool_call>')[1].split('\n')[0]}"
                            },
                            "fps": 2,
                            "media_resolution": "default"
                        },
                        {
                            "type": "text",
                            "text": lang.lang['bot.multimodel.viread']
                        }
                    ]
                }
    elif '<tool_call>videourl</tool_call>' in cmd:
        return {
                    "role": "user",
                    "content": [
                        {
                            "type": "video_url",
                            "video_url": {
                                "url": cmd.split('<tool_call>videourl</tool_call>')[1].split('\n')[0]
                            },
                            "fps": 2,
                            "media_resolution": "default"
                        },
                        {
                            "type": "text",
                            "text": lang.lang['bot.multimodel.viread']
                        }
                    ]
                }
    else:
        return {
                    "role":"user",
                    "content": cmd
                }

