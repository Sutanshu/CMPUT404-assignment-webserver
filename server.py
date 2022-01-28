#  coding: utf-8
import socketserver
import os
import mimetypes

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

# Author: Sutanshu Seth. Date last edited: Jan 28, 2022


def getRequestType(data):
    """
    Returns the HTTP Method type from the given request
    """
    return data[0].decode("utf-8")


def getFile(data):
    """
    Returns the path to the file for the given request
    """
    return data[1].decode("utf-8")


def isRequestValid(data):
    """
    Checks for empty request
    """
    return len(data) > 0


def isMethodAllowed(data):
    """
    Check if the method is allowed, as per assignment specs, only GET is allowed.
    Can be easily extended by removing or adding REST Methods to the list below
    """
    return getRequestType(data) in ["GET"]  # Can extend this for other methods


def errorCheck(code, data, dataFile=None):
    """
    A switch statement type function to check for error codes.
    Can be easily extended by adding more error codes and their corresponding checks.
    """
    specifiedFile = ""
    if dataFile:
        specifiedFile = dataFile
    else:
        specifiedFile = getFile(data)

    if code == "405":
        # Repeated for code readability, and function purpose
        return getRequestType(data) in ["GET"]

    if code == "404":
        # Checks if page isn't found as the file wouldn't exist
        return not os.path.exists(specifiedFile)

    if code == "301":
        # Checks if its not 404, so the path exists but the file does not
        if os.path.exists(specifiedFile):
            if not os.path.isfile(specifiedFile):
                return True


def getErrorResponse(code, renderFile=None):
    """
    Based on the error code, this function returns the response
    that is sent back to the client.
    """
    statusCodes = {
        "405": "405 - Method Not Allowed",
        "301": "Moved Permanently",
        "404": "Oops, wrong page! We don't have it!",
    }
    errorMessage = "<p1>{}</p1>"

    if code == "405":
        errorMessage = errorMessage.format(statusCodes[code])
        errorMessageLength = len(errorMessage.encode("utf-8"))
        response = (
            "HTTP/1.1 405 Method Not Allowed\r\nServer: Server Yoda's this is\r\nAllow: GET\r\nContent-length:"
            + str(errorMessageLength)
            + "\r\nContent-Type: text/html\r\n\r\n"
            + errorMessage
        )
        return response

    if code == "301":
        errorMessage = statusCodes[code]
        errorMessageLength = len(errorMessage.encode("utf-8"))
        if renderFile:
            if not renderFile[-1] == "/":
                renderFile += "/"
                if "www" in renderFile:
                    renderFile = renderFile[3:]
        response = f"HTTP/1.1 301 Moved Permanently\r\nServer: Server Yoda's this is\r\nLocation:http://127.0.0.1:8080{renderFile}\r\nConnection: close\r\n\r\n"
        return response

    if code == "404":
        errorMessage = errorMessage.format(statusCodes[code])
        errorMessageLength = len(errorMessage.encode("utf-8"))
        response = (
            "HTTP/1.1 404 Page Not Found\r\nServer: Server Yoda's this is\r\nContent-length:"
            + str(errorMessageLength)
            + "\r\nContent-type: text/html\r\n\r\n"
            + errorMessage
        )
        return response


def processGET(data):
    """
    This function processes the GET request.
    Checks if the file requested for is a mimetpye file.
    Returns a 404 response for files that don't exist,
    Or Returns 301 for moved files,
    Otherwise, it returns Success and the corresponding response with the file.
    """
    incomingFile = getFile(data)
    currentDirectory = os.path.join(os.getcwd(), "www")
    absolutePath = os.path.realpath(incomingFile)
    if "www" not in incomingFile:
        renderFile = "www" + incomingFile
    else:
        renderFile = incomingFile
    if renderFile[0] == "/":
        renderFile = renderFile[1:]
    response = ""

    if renderFile[-1] == "/":
        renderFile += "index.html"
    else:
        if errorCheck("301", data, renderFile):
            response = getErrorResponse("301", renderFile)
            return response
    contentType = mimetypes.guess_type(renderFile)

    try:
        # Check if the files to be served are only in www directory, if not, don't render
        # Source: (https://www.geeksforgeeks.org/python-os-path-commonprefix-method/ ,
        #         https://www.geeksforgeeks.org/python-os-path-realpath-method/)
        if not os.path.commonprefix([os.path.realpath(renderFile), absolutePath]) != currentDirectory:
            return getErrorResponse("404")

        fileObj = open(renderFile, "r").read().encode("utf-8")
        contentlength = str(len(fileObj))
        fileObj = fileObj.decode("utf-8")

        if contentType[0]:
            response = (
                "HTTP/1.1 200 OK\r\nServer: Server Yoda's this is\r\nContent-length:{}\r\nContent-Type:{}\r\n\r\n{}"
            ).format(contentlength, contentType[0], fileObj)
        else:
            # Not serving any non mime type files as per assignment specs
            # The file isn't a mimetype
            return getErrorResponse("404")

        return response
    except:
        if errorCheck("404", data):
            return getErrorResponse("404")


class MyWebServer(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        self.data = self.data.split()

        if not isRequestValid(self.data):
            return

        if not isMethodAllowed(self.data):
            errorMessage = getErrorResponse("405")
            self.request.sendall(bytearray(errorMessage, "utf-8"))
            return

        if isMethodAllowed(self.data):
            answer = processGET(self.data)
            self.request.sendall(bytearray(answer, "utf-8"))


if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
