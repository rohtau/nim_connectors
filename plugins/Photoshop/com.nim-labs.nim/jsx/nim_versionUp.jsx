/* *****************************************************************************
#
# Filename: Photoshop/NIM.jsx
# Version:  v2.5.0.161015
#
# Copyright (c) 2015 NIM Labs LLC
# All rights reserved.
#
# Use of this software is subject to the terms of the NIM Labs license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# *************************************************************************** */


// Shorter way of calling app.stringIDToTypeID
function s2t(stringID) {
  return app.stringIDToTypeID(stringID);
}


// Reads a file, returns its contents or false if it doesn't exist
function readFile(path) {
	var file = new File(path),
		fileString = '';
	if (file.exists) {
		file.open('r');
		fileString = file.read();
		file.close();
		return fileString;
	}
	else return false;
}


// Gives user a dialogue box to enter a scripts path and API URL; verifies that both are valid or warns user that NIM won't work;
// pass it 'nimPrefs', an object containing 'error' (error message for user) and optionally either 'scriptsPath' or 'API';
// will populate appropriate input boxes given 'scriptsPath' or 'API'
function prefsDialog(nimPrefs, thisObj) {
	var createPrefsDialog = new Window('dialog', 'NIM', undefined),
		createPrefsLabel = createPrefsDialog.add('statictext', undefined, nimPrefs.error),
		scriptsPathGroup = createPrefsDialog.add('group', undefined),
		scriptsPathLabel = scriptsPathGroup.add('statictext', undefined, 'Scripts path: '),
		scriptsPathInput = scriptsPathGroup.add('edittext', [0, 0, 250, 20]),
		APIPathGroup = createPrefsDialog.add('group', undefined),
		APIPathLabel = APIPathGroup.add('statictext', undefined, 'API URL: '),
		APIPathInput = APIPathGroup.add('edittext', [0, 0, 250, 20]),
		buttonGroup = createPrefsDialog.add('group', undefined),
		confirmButton = buttonGroup.add('button', undefined, 'OK'),
		cancelButton = buttonGroup.add('button', undefined, 'Cancel');

	if (nimPrefs.scriptsPath)
		scriptsPathInput.text = nimPrefs.scriptsPath;
	if (nimPrefs.API)
		APIPathInput.text = nimPrefs.API;

	confirmButton.onClick = function() {
		nimPrefs.scriptsPath = scriptsPathInput.text;
		nimPrefs.API = APIPathInput.text;
		nimAPIURL = nimPrefs.API;
		saveScriptsPathAndAPIToPrefs();

		var remoteScripts = getRemoteScripts(scriptsPathInput.text, thisObj),
			nimMenuPanel;
		
		if (remoteScripts !== false) {
			nimMenuPanel = remoteScripts(thisObj);
			if (nimMenuPanel) {
				// Success!
			}
		}

		createPrefsDialog.close();
	}

	cancelButton.onClick = function() {
		alert("Your files won't be connected to NIM until you have a valid preferences file.");
		createPrefsDialog.close();
	}

	createPrefsDialog.show();
}


// Returns either an object containing 'scriptsPath' and 'API' or an object containing 'error',
// an error message for the dialog box that will prompt user for scripts path and API URL
function getScriptsPathAndAPIFromPrefs() {
	var nimPrefsFile = new File(nimPrefsPath),
		currentLine,
		scriptsPos,
		apiPos,
		foundScripts = false,
		foundAPI = false;

	if (!nimPrefsFile.exists)
		return { error: 'NIM preferences file not found. To create a new one, please enter the following info:' };

	nimPrefsFile.open('r');
	while (!nimPrefsFile.eof) {
		currentLine = nimPrefsFile.readln();
		if (!foundScripts) {
			scriptsPos = currentLine.indexOf('NIM_Scripts=');
			if (scriptsPos != -1)
				foundScripts = currentLine.substr(scriptsPos + 12);
		}
		if (!foundAPI) {
			apiPos = currentLine.indexOf('NIM_URL=');
			if (apiPos != -1)
				foundAPI = currentLine.substr(apiPos + 8);
		}
		if (foundScripts && foundAPI) break;
	}
	nimPrefsFile.close();

	if (foundScripts && foundAPI)
		return { scriptsPath: foundScripts, API: foundAPI };
	else if (foundScripts)
		return { scriptsPath: foundScripts, error: "NIM preferences file doesn't contain an API URL. Please enter one below:" };
	else if (foundAPI)
		return { API: foundAPI, error: "NIM preferences file doesn't contain a scripts path. Please enter one below:" }
	else
		return { error: "NIM preferences file doesn't contain a scripts path or an API URL. Please enter them below:" }
}


// Does what function title says; gets 'scriptsPath' and 'API' strings from 'nimPrefs' global object
function saveScriptsPathAndAPIToPrefs() {
	var nimPrefsFile = new File(nimPrefsPath),
		nimPrefsFileTemp,
		nimPrefsFileTempPath = nimPrefsPath + 'temp',
		currentLine,
		scriptsPos,
		apiPos,
		scriptsPath = nimPrefs.scriptsPath,
		apiPath = nimPrefs.API,
		foundScripts = false,
		foundAPI = false;

	if (!nimPrefsFile.exists) {
		createNimPrefsFile();
	}

	nimPrefsFile.copy(nimPrefsFileTempPath);
	nimPrefsFileTemp = new File(nimPrefsFileTempPath);
	if (!nimPrefsFileTemp.open('r'))
		return false;

	nimPrefsFile.lineFeed = 'Unix';
	nimPrefsFile.open('w');
	while (!nimPrefsFileTemp.eof) {
		currentLine = nimPrefsFileTemp.readln();
		if (!foundScripts) {
			scriptsPos = currentLine.indexOf('NIM_Scripts=');
			if (scriptsPos != -1) {
				foundScripts = true;
				currentLine = currentLine.substr(0, scriptsPos + 12) + scriptsPath;
			}
		}
		if (!foundAPI) {
			apiPos = currentLine.indexOf('NIM_URL=');
			if (apiPos != -1) {
				foundAPI = true;
				currentLine = currentLine.substr(0, apiPos + 8) + apiPath;
			}
		}
		nimPrefsFile.writeln(currentLine);
	}
	nimPrefsFileTemp.close();
	nimPrefsFile.close();
	nimPrefsFileTemp.remove();
	return true;
}


function createNimPrefsFile() {
	var nimPrefsFolder = new Folder(nimPrefsFolderPath),
		nimPrefsFile = new File(nimPrefsPath);

	if (!nimPrefsFolder.exists)
		nimPrefsFolder.create();

	nimPrefsFile.lineFeed = 'Unix';
	nimPrefsFile.open('w');
	
	nimPrefsFile.writeln('NIM_URL=');
	nimPrefsFile.writeln('NIM_User=');
	nimPrefsFile.writeln('NIM_Scripts=');
	nimPrefsFile.writeln('NIM_UserScripts=');
	nimPrefsFile.writeln('NIM_DebugMode=False');
	nimPrefsFile.writeln('NIM_Thumbnail=');

	nimPrefsFile.close();
	return true;
}


function getKeyFromPrefs() {
	var nimKeyFile = new File(nimKeyPath),
		nimKey = '',
		foundScripts = false,
		foundAPI = false;

	if (!nimKeyFile.exists)
		return '';

	nimKeyFile.open('r');
	nimKey = nimKeyFile.readln();    
	nimKeyFile.close();

	if (!nimKey)
		nimKey = '';

	return nimKey;
}


// Returns a function that takes one argument (thisObj) and generates the NIM menu / contains all NIM functions
function getRemoteScripts(scriptsPath) {
	var nimMainPath = 'nimMain.jsx',
		nimPanelPath = 'nimPanel.jsx',
		nimMenuPath = 'nimMenu.jsx',
		scriptsFolder = new Folder(scriptsPath);

	if (!scriptsFolder.exists) {
		nimPrefs.error = "The scripts path in NIM preferences doesn't exist; it should be the path to a valid directory containing NIM's script files.";
		prefsDialog(nimPrefs, thisObj);
		return false;
	}

	// Make sure last character of scriptsPath is '/' (or '\' if path contains only backslashes)
	// and 'Photoshop' folder is appended
	var lastChar = scriptsPath.slice(-1);
	while (lastChar == '/' || lastChar == '\\') {
		scriptsPath = scriptsPath.slice(0, -1);
		lastChar = scriptsPath.slice(-1);
	}
	if (scriptsPath.indexOf('\\') != -1 && scriptsPath.indexOf('/') == -1)
		scriptsPath += '\\plugins\\Photoshop\\';
	else
		scriptsPath += '/plugins/Photoshop/';


	var nimMainContents = readFile(scriptsPath + nimMainPath),
		nimPanelContents = readFile(scriptsPath + nimPanelPath),
		nimMenuContents = readFile(scriptsPath + nimMenuPath),
		missingScripts = [],
		missingScriptsLength,
		missingScriptsMessage,
		remoteScripts;

	if (nimMainContents === false)
		missingScripts.push(nimMainPath);
	if (nimPanelContents === false)
		missingScripts.push(nimPanelPath);

	missingScriptsLength = missingScripts.length;
	if (missingScriptsLength) {
		missingScriptsMessage = 'Your scripts folder is missing the following files: ';
		for (var x = 0; x < missingScriptsLength; x++)
			missingScriptsMessage += 'plugins/Photoshop/' + missingScripts[x] + ', ';
		nimPrefs.error = missingScriptsMessage.slice(0, -2);
		prefsDialog(nimPrefs, thisObj);
		return false;
	}

	remoteScripts = function(thisObj) {
		var apiTest;
		eval(nimMainContents);
		if (typeof nimAPI != 'undefined')
			apiTest = nimAPI({ q: 'testAPI' });
		if (apiTest == 'keyError')
			return false;  // If we have an error with API key, error will be triggered from nimAPI function
		if (typeof apiTest == 'object' && apiTest.length && typeof apiTest[0] == 'object' && apiTest[0].error == '')
			eval(nimPanelContents);
		else {
			nimPrefs.error = "The NIM API was not found at given URL; please provide a valid URL to NIM's API.";
			prefsDialog(nimPrefs, thisObj);
			return false;
		}
		if (typeof buildPanelUI != 'undefined') {


// ===================================================================================================================

			try { activeDocument; }
			catch(e) {
				if (loadingPanel) loadingPanel.close();
				alert('No file open! Please open a file before attempting to version up.');
				return;
			}
			var metadata = getNimMetadata(),
				comment;
			if (!metadata.classID) {
				if (loadingPanel) loadingPanel.close();
				alert("Error: This file doesn't have any NIM metadata; please save it through the NIM menu before attempting to version up.");
				return;
			}

			/*
			commentDialog(function(comment, addElement) {
				if (comment === false) return;
				if (saveFile(metadata.classID, metadata.className, metadata.serverID, metadata.serverPath, metadata.taskID, metadata.taskFolder, metadata.basename, comment, false, addElement))
					alert('New version saved.');
				else
					alert('Error: Version up failed!');
			});
			*/

			return buildPanelUI(userID, 'versionUp', metadata);

// ===================================================================================================================


		}
		else {
			alert('Error: Script loading failed!');
			return false;
		}
	}

	return remoteScripts;
}

try { var testSocket = new Socket; }
catch (e) {
	alert('Error: Sockets not working with Photoshop!');
	testSocket = false;
}

if (testSocket) {
	var nimPrefsFolderPath = '~/.nim/',
		nimPrefsPath = nimPrefsFolderPath + 'prefs.nim',
		nimKeyPath = nimPrefsFolderPath + 'nim.key',
		nimPrefs = getScriptsPathAndAPIFromPrefs(),
		nimKey = getKeyFromPrefs(),
		remoteScripts,
		nimScriptsPath,
		nimAPIURL,
		thisObj = this;

		menuClosed = false;

	if (nimPrefs.error)
		prefsDialog(nimPrefs, this);
	else {
		nimScriptsPath = nimPrefs.scriptsPath;
		nimAPIURL = nimPrefs.API;

		// Remove question mark(s) from end of API URL
		while (nimAPIURL.slice(-1) == '?')
			nimAPIURL = nimAPIURL.slice(0, -1);

		remoteScripts = getRemoteScripts(nimPrefs.scriptsPath, this);

		if (remoteScripts !== false) {
			remoteScripts(this);
			// This next line necessary if we're trying to make the nimMenu a "palette" instead of a "dialog"
			// http://www.davidebarranca.com/2012/10/scriptui-window-in-photoshop-palette-vs-dialog/
			//while (menuClosed === false) app.refresh();
		}
	}
}

