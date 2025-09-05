import time
from email.utils import formatdate

# DateTime utils
now = time.time()
http_date = formatdate(timeval=now, localtime=False, usegmt=True)


# parser_HTTP_message: string -> dict[string, List[string], string]
# Simple HTTP message parser, returns a dictionary with start line and headers
def parse_HTTP_message(http_message):
    separator = "\r\n\r\n"
    if separator in http_message:
        headers_part, body = http_message.split(separator, 1)
    else:
        headers_part = http_message
        body = ""

    # Tomamos la start line y los headers
    lines = headers_part.split("\r\n")
    start_line = lines[0]
    headers = lines[1:]  # el resto son headers

    return {
        "start_line": start_line,  # string
        "headers": headers,        # list de strings
        "body": body               # string
    }

# create_HTTP_message: dict -> string
# Simple HTTP message creator from a dictionary
def create_HTTP_message(http_dataStruct):
    message = http_dataStruct["start_line"]+"\r\n"
    for header in http_dataStruct["headers"]:
        message += header + "\r\n"
    message += "\r\n"
    message += http_dataStruct.get("body", "") 
    return message

# create_HTTP_response: string string -> string
# Creates a full HTTP response message with given HTML body
def create_HTTP_response(html, name="?"):
    html_body = html.replace("{{name}}", name)
    start_line = f"HTTP/1.1 200 OK\r\n"
    headers = [
        "Server: Simple-Python-HTTP-Server\r\n",
        f"Date: {http_date}\r\n",
        f"Content-Length: {len(html_body.encode('utf-8'))}\r\n",
        "Content-Type: text/html; charset=UTF-8\r\n",
        "Connection: keep-alive\r\n",
        f"X-ElQuePregunta: {name}\r\n",
    ]
    return f"{start_line}{''.join(headers)}\r\n{html_body}"
