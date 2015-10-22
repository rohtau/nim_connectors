/* ****************************************************************************
#
# Filename: Photoshop/nimPanel.jsx
# Version:  v0.7.3.150625
#
# Copyright (c) 2015 NIM Labs LLC
# All rights reserved.
#
# Use of this software is subject to the terms of the NIM Labs license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# *************************************************************************** */

function buildPanelUI(userID, action) {

	// Populates a dropdown with the strings stored under the nameField key in the objects
	// contained in dataArray; defaultMessage will be the first dropdown item if items exist
	function populateDropdown(dropdown, dataArray, nameField, defaultMessage) {
		var dataArrayLength = dataArray.length;
		dropdown.removeAll();
		dropdown.add('item', defaultMessage);
		if (dataArrayLength && dataArray[0].ID == 0) {
			dataArray.shift();
			dataArrayLength = dataArray.length;
		}
		if (nameField instanceof Array) {
			var nameFieldLength = nameField.length;
			for (var x = 0; x < dataArrayLength; x++) {
				var thisItemName = [];
				for (var y = 0; y < nameFieldLength; y++)
					thisItemName.push(dataArray[x][nameField[y]]);
				dropdown.add('item', thisItemName.join('_'));
			}
		}
		else {
			for (var x = 0; x < dataArrayLength; x++)
				dropdown.add('item', dataArray[x][nameField]);
		}
		if (dropdown.items.length == 1) {
			dropdown.removeAll();
			dropdown.add('item', 'None');
			dropdown.enabled = false;
		}
		else {
			dropdown.enabled = true;
			dataArray.unshift({ ID: 0 });
		}
		dropdown.selection = 0;
	}

	// Populates a listbox with the strings stored under the nameField key in the objects
	// contained in dataArray
	function populateListbox(listbox, dataArray, nameField) {
		var dataArrayLength = dataArray.length;
		listbox.removeAll();
		if (nameField instanceof Array) {
			var nameFieldLength = nameField.length;
			for (var x = 0; x < dataArrayLength; x++) {
				var thisItemName = [];
				for (var y = 0; y < nameFieldLength; y++) {
					var thisNamePiece = dataArray[x][nameField[y]];
					if (thisNamePiece)
						thisItemName.push(thisNamePiece);
				}
				listbox.add('item', thisItemName.join(' - '));
			}
		}
		else {
			for (var x = 0; x < dataArrayLength; x++)
				listbox.add('item', dataArray[x][nameField]);
		}
		if (!listbox.items.length)
			listbox.enabled = false;
		else
			listbox.enabled = true;
	}

	// Clears text fields in versionInfo panel (and saved filepath variable), disable confirm button
	function clearVersionInfo() {
		filepath = '';
		if (pathText) pathText.text = '';
		if (userText) userText.text = '';
		if (dateText) dateText.text = '';
		if (commentText) commentText.text = '';
	}

	// Sets initial dropdown or listbox ('container') selection to item with 'property' equal to 'value' within 'array'
	// (of objects that initially populated dropdown or listbox)
	function setInitialSelection(property, value, array, container) {
		if (value) {
			var arrayLength = array.length;
			for (var x = 0; x < arrayLength; x++) {
				if (array[x][property] == value) {
					container.selection = x;
					container.onChange();
					return true;
				}
			}
		}
		return false;
	}

	function setPanelPrefs() {
		setPref('Photoshop', 'jobID', jobID);
		if (action == 'saveAs') setPref('Photoshop', 'serverID', serverID);
		setPref('Photoshop', 'assetID', assetID);
		setPref('Photoshop', 'showID', showID);
		setPref('Photoshop', 'shotID', shotID);
		setPref('Photoshop', 'taskID', taskID);
		setPref('Photoshop', 'showPub', showPub);
		setPref('Photoshop', 'basename', basename);
	}

	var nimPanel = new Window('dialog', 'NIM', undefined),
		jobs = nimAPI({ q: 'getUserJobs', u: userID }),
		servers,
		assets = [],
		shows = [],
		shots = [],
		tasks = nimAPI({ q: 'getTaskTypes', type: 'artist', app: 'Photoshop' }),
		basenames = [],
		versions = [],
		jobID = 0,
		serverID = 0,
		serverPath = '',
		assetID = 0,
		assetName = '',
		showID = 0,
		shotID = 0,
		shotName = '',
		taskID = 0,
		taskFolder = '',
		showPub = 0,
		basename = '',
		maxVersion = 0,
		filepath = '',
		fileID = 0,
		jobTaskInfo = nimPanel.add('group', undefined),
		jobInfo = jobTaskInfo.add('panel', undefined, 'Job Info'),
		jobDropdown = jobInfo.add('dropdownlist', undefined, '', { items: ['None'] }),
		serverDropdown = jobInfo.add('dropdownlist', undefined, '', { items: ['None'] }),
		jobTabPanel = jobInfo.add('tabbedpanel'),
		assetsTab = jobTabPanel.add('tab', undefined, 'Assets'),
		assetDropdown = assetsTab.add('dropdownlist', undefined, '', { items: ['None'] }),
		//assetMasterButton,
		shotsTab = jobTabPanel.add('tab', undefined, 'Shots'),
		showDropdown = shotsTab.add('dropdownlist', undefined, '', { items: ['None'] }),
		shotDropdown = shotsTab.add('dropdownlist', undefined, '', { items: ['None'] }),
		taskInfo = jobTaskInfo.add('panel', undefined, 'Task Info'),
		filterDropdown = taskInfo.add('dropdownlist', undefined, '', { items: ['Work', 'Published'] }),
		taskDropdown = taskInfo.add('dropdownlist', undefined, '', { items: ['None'] }),
		basenameGroup = taskInfo.add('group', undefined),
		basenameListboxLabel = basenameGroup.add('statictext', undefined, 'Basename: '),
		basenameListbox = basenameGroup.add('listbox', [0, 0, 250, 200], 'Basename'),
		tagGroup,
		tagLabel,
		tagInput,
		outputFiles = nimPanel.add('tabbedpanel'),
		versionInfo = outputFiles.add('tab', undefined, 'Version Info'),
		versionGroup = versionInfo.add('group', undefined),
		versionListboxLabel = versionGroup.add('statictext', undefined, 'Versions: '),
		versionListbox = versionGroup.add('listbox', [0, 0, 550, 250], 'Versions'),
		pathGroup = versionInfo.add('group', undefined),
		pathLabel = pathGroup.add('statictext', undefined, 'Path: '),
		pathText = pathGroup.add('statictext', [0, 0, 550, 20], ''),
		userGroup = versionInfo.add('group', undefined),
		userLabel = userGroup.add('statictext', undefined, 'User: '),
		userText = userGroup.add('statictext', [0, 0, 550, 20], ''),
		dateGroup = versionInfo.add('group', undefined),
		dateLabel = dateGroup.add('statictext', undefined, 'Date: '),
		dateText = dateGroup.add('statictext', [0, 0, 550, 20], ''),
		commentGroup = versionInfo.add('group', undefined),
		commentLabel = commentGroup.add('statictext', undefined, 'Comment: '),
		commentText,
		commentInput,
		fileTypeDropdown,
		elementsToAdd,
		elementSelectionGroup,
		elementButtonGroup,
		elementFileTypeDropdown,
		elementAddButton,
		elementEditButton,
		elementDeleteButton,
		elementListboxGroup,
		elementListboxLabel,
		elementListbox,
		elementDetailsDialog,
		elementDetailsPanel,
		elementExports,
		allDropdowns = [jobDropdown, serverDropdown, assetDropdown, showDropdown, shotDropdown, taskDropdown, filterDropdown],
		allDropdownsLength = allDropdowns.length,
		buttonGroup = nimPanel.add('group', undefined),
		confirmButton = buttonGroup.add('button', undefined, 'Confirm'),
		cancelButton = buttonGroup.add('button', undefined, 'Cancel');

	jobDropdown.title = 'Job: ';
	//serverDropdown.title = 'Server: ';
	assetDropdown.title = 'Asset: ';
	showDropdown.title = 'Show: ';
	shotDropdown.title = 'Shot: ';
	taskDropdown.title = 'Task: ';
	//filterDropdown.title = 'Filter: ';

	serverDropdown.enabled = false;
	assetDropdown.enabled = false;
	showDropdown.enabled = false;
	shotDropdown.enabled = false;
	taskDropdown.enabled = false;
	filterDropdown.enabled = false;
	basenameListbox.enabled = false;
	versionListbox.enabled = false;
	confirmButton.enabled = false;

	nimPanel.alignChildren = 'fill';
	versionInfo.alignChildren = 'right';
	jobTaskInfo.alignChildren = 'fill';
	taskInfo.alignChildren = 'right';
	basenameGroup.alignChildren = 'top';
	versionGroup.alignChildren = 'top';
	
	versionGroup.alignment = 'right';
	pathGroup.alignment = 'right';
	userGroup.alignment = 'right';
	dateGroup.alignment = 'right';
	commentGroup.alignment = 'right';
	buttonGroup.alignment = 'right';

	populateDropdown(jobDropdown, jobs, ['number', 'jobname'], 'Select a job...');

	for (var x = 0; x < allDropdownsLength; x++) {
		allDropdowns[x].preferredSize[0] = 289;
		allDropdowns[x].selection = 0;
	}

	assetDropdown.preferredSize[0] = 250;
	showDropdown.preferredSize[0] = 250;
	shotDropdown.preferredSize[0] = 250;


	// Customize panel based on action
	if (!action)
		action = 'open';

	if (action == 'open' /*|| action == 'import'*/) {
		commentText = commentGroup.add('statictext', [0, 0, 550, 20], '');
		jobInfo.remove(serverDropdown);
		serverDropdown = null;	
		/*if (action == 'open')*/ confirmButton.text = 'Open File';
		/*
		else if (action == 'import') {
			confirmButton.text = 'Import File';
			assetMasterButton = assetsTab.add('button', undefined, 'Import Asset Master');
			assetMasterButton.enabled = false;
			assetMasterButton.alignment = 'fill';
		}
		*/
	}
	else if (action == 'saveAs') {
		taskInfo.remove(filterDropdown);
		filterDropdown = null;
		tagGroup = taskInfo.add('group', undefined);
		tagLabel = tagGroup.add('statictext', undefined, 'Tag: ');
		tagInput = tagGroup.add('edittext', [0, 0, 250, 20]);
		versionInfo.remove(pathGroup);
		versionInfo.remove(userGroup);
		versionInfo.remove(dateGroup);
		pathText = null;
		userText = null;
		dateText = null;
		commentInput = commentGroup.add('edittext', [0, 0, 550, 20]);
		elementsToAdd = outputFiles.add('tab', [0, 0, 687, 250], 'Export Elements');
		elementsToAdd.orientation = 'row';
		elementsToAdd.alignChildren = 'fill';
		outputFiles.selection = versionInfo;
		elementSelectionGroup = elementsToAdd.add('group', undefined);
		elementSelectionGroup.orientation = 'column';
		elementSelectionGroup.alignChildren = 'left';
		elementButtonGroup = elementSelectionGroup.add('group', undefined);
		elementFileTypeDropdown = elementButtonGroup.add('dropdownlist', undefined, '', { items: ['Photoshop (.psd)', 'EPS', 'GIF', 'JPEG (.jpg)', 'PNG', 'RAW', 'Targa (.tga)', 'TIFF (.tif)'] });
		elementFileTypeDropdown.selection = 0;
		elementAddButton = elementButtonGroup.add('button', undefined, 'Add Element');
		fileID = getMetadata('fileID');
		elementExports = nimAPI({ q: 'getElementExports', fileID: fileID || 0 }) || [];

		elementListboxGroup = elementSelectionGroup.add('group', undefined);
		elementListboxGroup.alignChildren = 'top';
		elementListboxLabel = elementListboxGroup.add('statictext', undefined, 'Elements: ');
		elementListbox = elementListboxGroup.add('listbox', [0, 0, 250, 236], 'Elements');

		elementDetailsGroup = elementsToAdd.add('group', undefined);
		elementDetailsGroup.orientation = 'column';
		elementDetailsGroup.alignChildren = 'fill';
		elementDetailsGroup.margins = [10, 0, 0, 10];

		elementDetailsButtonGroup = elementDetailsGroup.add('group', undefined);

		elementEditButton = elementDetailsButtonGroup.add('button', undefined, 'Edit Element');
		elementDeleteButton = elementDetailsButtonGroup.add('button', undefined, 'Delete Element');
		elementEditButton.enabled = false;
		elementDeleteButton.enabled = false;

		elementDetailsPanel = elementDetailsGroup.add('panel', [0, 0, 345, 255], 'Element Details');
		elementDetailsPanel.margins = [10, 0, 0, 10];

		confirmButton.text = 'Save As';

		var elementExportsLength = elementExports.length;

		for (var x = 0; x < elementExportsLength; x++) {
			var thisExtension = elementExports[x].extension,
				thisExtensionName = thisExtension;
			if (thisExtension == 'psd')
				thisExtensionName = 'Photoshop (.psd)';
			else if (thisExtension == 'eps')
				thisExtensionName = 'EPS';
			else if (thisExtension == 'gif')
				thisExtensionName = 'GIF';
			else if (thisExtension == 'jpg')
				thisExtensionName = 'JPEG (.jpg)';
			else if (thisExtension == 'png')
				thisExtensionName = 'PNG';
			else if (thisExtension == 'raw')
				thisExtensionName = 'RAW';
			else if (thisExtension == 'tga')
				thisExtensionName = 'Targa (.tga)';
			else if (thisExtension == 'tif')
				thisExtensionName = 'TIFF (.tif)';
			elementListbox.add('item', thisExtensionName);
		}
	}


	// Add events to elements
	jobDropdown.onChange = function() {
		if (!this.selection || !this.selection.index) {
			jobID = 0;
			if (serverDropdown) {
				populateDropdown(serverDropdown, [], '', '');
				serverDropdown.enabled = false;
			}
			populateDropdown(assetDropdown, [], '', '');
			populateDropdown(showDropdown, [], '', '');
			return;
		}
		jobID = jobs[this.selection.index].ID;
		assets = nimAPI({ q: 'getAssets', ID: jobID });
		shows = nimAPI({ q: 'getShows', ID: jobID });
		populateDropdown(assetDropdown, assets, 'name', 'Select an asset...');
		populateDropdown(showDropdown, shows, 'showname', 'Select a show...');
		if (serverDropdown) {
			servers = nimAPI({ q: 'getJobServers', ID: jobID });
			populateDropdown(serverDropdown, servers, 'server', 'Select a server...');
			if (serverDropdown.items.length == 1)
				serverDropdown.enabled = false;
			else
				serverDropdown.enabled = true;
		}
	}

	if (serverDropdown) {
		serverDropdown.title = 'Server: ';
		serverDropdown.onChange = function() {
			if (!this.selection || !this.selection.index) {
				serverID = 0;
				serverPath = '';
				confirmButton.enabled = false;
				return;
			}
			serverID = servers[this.selection.index].ID;
			if (os == 'win')
				serverPath = servers[this.selection.index].winPath;
			else if (os == 'mac')
				serverPath = servers[this.selection.index].osxPath;
			else
				serverPath = servers[this.selection.index].path;
			if (taskID)
				confirmButton.enabled = true;
		}
	}

	showDropdown.onChange = function() {
		if (!this.selection || !this.selection.index) {
			showID = 0;
			populateDropdown(shotDropdown, [], '', '');
			return;
		}
		showID = shows[this.selection.index].ID;
		shots = nimAPI({ q: 'getShots', ID: showID });
		populateDropdown(shotDropdown, shots, 'name', 'Select a shot...');
		//if (assetMasterButton)
		//	assetMasterButton.enabled = false;
	}

	assetDropdown.onChange = function() {
		if (!this.selection || !this.selection.index) {
			assetID = 0;
			assetName = '';
			if (!shotID) {
				populateDropdown(taskDropdown, [], '', '');
				if (filterDropdown) filterDropdown.enabled = false;
			}
			return;
		}
		shotID = 0;
		shotName = '';
		shotDropdown.selection = 0;
		assetID = assets[this.selection.index].ID;
		assetName = assets[this.selection.index].name;
		populateDropdown(taskDropdown, tasks, 'name', 'Select a task...');
		if (filterDropdown)
			filterDropdown.enabled = true;
		//if (assetMasterButton)
		//	assetMasterButton.enabled = true;
	}

	/*
	if (assetMasterButton) {
		assetMasterButton.onClick = function() {
			var assetMaster = nimAPI({ q: 'getAssetMasterOSPath', assetID: assetID, os: os }),
				assetMasterPath,
				assetMasterFile;
			if (assetMaster == 0) {
				alert('Error: No asset master found!');
				return;
			}
			assetMasterPath = assetMaster.path;
			assetMasterFile = new File(assetMasterPath);
			if (!assetMasterFile.exists) {
				alert('Error: Asset master symbolic link not found at "' + assetMasterPath + '"!');
				return;
			}
			try { app.project.importFile(new ImportOptions(assetMasterFile)); }
			catch (e) {
				alert(e);
				return;
			}
			nimPanel.close();
		}
	}
	*/

	shotDropdown.onChange = function() {
		if (!this.selection || !this.selection.index) {
			shotID = 0;
			shotName = '';
			if (!assetID) {
				populateDropdown(taskDropdown, [], '', '');
				if (filterDropdown) filterDropdown.enabled = false;
			}
			return;
		}
		assetID = 0;
		assetName = '';
		assetDropdown.selection = 0;
		shotID = shots[this.selection.index].ID;
		shotName = shots[this.selection.index].name;
		populateDropdown(taskDropdown, tasks, 'name', 'Select a task...');
		if (filterDropdown)
			filterDropdown.enabled = true;
	}

	taskDropdown.onChange = function() {
		if (!this.selection || !this.selection.index) {
			taskID = 0;
			taskFolder = '';
			basename = '';
			maxVersion = 0;
			populateListbox(basenameListbox, [], '');
			populateListbox(versionListbox, [], '');
			clearVersionInfo();
			confirmButton.enabled = false;
			return;
		}
		var classID, className;
		if (assetID) {
			classID = assetID;
			className = 'ASSET';
		}
		else if (shotID) {
			classID = shotID;
			className = 'SHOT';
		}
		taskID = tasks[this.selection.index].ID;
		taskFolder = tasks[this.selection.index].folder;
		if (showPub)
			basenames = nimAPI({ q: 'getBasenameAllPub', task_type_ID: taskID, itemID: classID, 'class': className });
		else
			basenames = nimAPI({ q: 'getBasenamesInfo', task_type_ID: taskID, ID: classID, 'class': className });
		populateListbox(basenameListbox, basenames, 'basename');
		populateListbox(versionListbox, [], '');
		if (serverID) {
			if (tagInput && tagInput.text)
				basenameListbox.enabled = false;
			confirmButton.enabled = true;
		}
		else confirmButton.enabled = false;
	}

	if (filterDropdown) {
		filterDropdown.title = 'Filter: ';
		filterDropdown.onChange = function() {
			var classID, className;
			if (assetID) {
				classID = assetID;
				className = 'ASSET';
			}
			else if (shotID) {
				classID = shotID;
				className = 'SHOT';
			}
			if (this.selection.text == 'Published') {
				showPub = 1;
				if (!taskID) return;
				basenames = nimAPI({ q: 'getBasenameAllPub', task_type_ID: taskID, itemID: classID, 'class': className });
			}
			else {
				showPub = 0;
				if (!taskID) return;
				basenames = nimAPI({ q: 'getBasenames', task_type_ID: taskID, ID: classID, 'class': className });
			}
			basename = '';
			maxVersion = 0;
			populateListbox(basenameListbox, basenames, 'basename');
			populateListbox(versionListbox, [], '');
			clearVersionInfo();
			confirmButton.enabled = false;
		}
	}

	basenameListbox.onChange = function() {
		if (!this.selection) {
			basename = '';
			maxVersion = 0;
			populateListbox(versionListbox, [], '');
			clearVersionInfo();
			if (action != 'saveAs') confirmButton.enabled = false;
			return;
		}
		var classID, className;
		if (assetID) {
			classID = assetID;
			className = 'ASSET';
		}
		else if (shotID) {
			classID = shotID;
			className = 'SHOT';
		}
		basename = basenames[this.selection.index].basename;
		maxVersion = basenames[this.selection.index].maxVersion;
		versions = nimAPI({ q: 'getVersions', itemID: classID, type: className, basename: basename, pub: showPub });
		populateListbox(versionListbox, versions, ['filename', 'note']);
		if (serverID && action == 'saveAs')
			versionListbox.enabled = false;
		// Select published version if published filter is on
		else if (filterDropdown && showPub) {
			var publishedFile = basenames[this.selection.index],
				publishedFileName = publishedFile.filename,
				versionListboxChildren = versionListbox.children,
				versionListboxChildrenLength = versionListboxChildren.length;
			for (var x = 0; x < versionListboxChildrenLength; x++) {
				if (versionListboxChildren[x].text.indexOf(publishedFileName) != -1) {
					versionListbox.selection = versionListboxChildren[x];
					versionListbox.selection.text += ' (PUBLISHED)';
					break;
				}
			}
		}
	}

	if (tagInput) {
		tagInput.onChanging = function() {
			if (!this.text) {
				if (serverID && taskID) basenameListbox.enabled = true;
				return;
			}
			basenameListbox.selection = null;
			basenameListbox.enabled = false;
		}
	}

	versionListbox.onChange = function() {
		if (!this.selection) {
			clearVersionInfo();
			confirmButton.enabled = false;
			return;
		}
		var thisVersion = versions[this.selection.index],
			thisFilepath,
			filepathObj = nimAPI({ q: 'getOSPath', fileID: thisVersion.fileID, os: os });
		if (filepathObj == 0)
			thisFilepath = thisVersion.filepath;
		else
			thisFilepath = filepathObj.path;
		filepath = thisFilepath + thisVersion.filename;
		pathText.text = thisFilepath;
		userText.text = thisVersion.username;
		dateText.text = thisVersion.date;
		if (commentText) commentText.text = thisVersion.note;
		confirmButton.enabled = true;
	}

	if (elementsToAdd) {
		elementFileTypeDropdown.onChange = function() {
			if (this.selection == 0) {
				/*
				var allElementDetailPanelsLength = allElementDetailPanels.length;
				for (var x = 0; x < allElementDetailPanelsLength; x++) {
					//allElementDetailPanels[x].hide();
				}
				pngPanel.show();
				*/
			}
		}

		elementAddButton.onClick = function() {
			elementListbox.add('item', elementFileTypeDropdown.selection.text);

			var thisExtension = 'psd';
			if (elementFileTypeDropdown.selection.index == 1)
				thisExtension = 'eps';
			else if (elementFileTypeDropdown.selection.index == 2)
				thisExtension = 'gif';
			else if (elementFileTypeDropdown.selection.index == 3)
				thisExtension = 'jpg';
			else if (elementFileTypeDropdown.selection.index == 4)
				thisExtension = 'png';
			else if (elementFileTypeDropdown.selection.index == 5)
				thisExtension = 'raw';
			else if (elementFileTypeDropdown.selection.index == 6)
				thisExtension = 'tga';
			else if (elementFileTypeDropdown.selection.index == 7)
				thisExtension = 'tif';

			// Add this item to the elementExports array
			elementExports.push({
				extension: thisExtension
			});
		}

		elementEditButton.onClick = function() {
			elementDetailsDialog = new Window('dialog', 'Element Details', undefined);
			
			var elementDetailsPanelButtonGroup = elementDetailsDialog.add('group', undefined),
				elementDetailsOkButton = elementDetailsPanelButtonGroup.add('button', undefined, 'OK'),
				elementDetailsCancelButton = elementDetailsPanelButtonGroup.add('button', undefined, 'Cancel');
			
			elementDetailsOkButton.onClick = function() {

				// TODO: modify elementExports array to reflect changes

				elementDetailsDialog.close();
			}

			elementDetailsCancelButton.onClick = function() {
				elementDetailsDialog.close();
			}

			elementDetailsDialog.show();
		}

		elementDeleteButton.onClick = function() {

			var indexToRemove = elementListbox.selection.index;
			
			// Remove this item from the elementExports array
			elementExports.splice(indexToRemove, 1);

			elementListbox.remove(elementListbox.selection);
			elementEditButton.enabled = false;
			elementDeleteButton.enabled = false;
		}

		elementListbox.onChange = function() {
			if (this.selection) {
				elementEditButton.enabled = true;
				elementDeleteButton.enabled = true;
			}
			else {
				elementEditButton.enabled = false;
				elementDeleteButton.enabled = false;
			}
		}
	}

	confirmButton.onClick = function() {
		if (action == 'open') {
			if (!filepath) {
				alert('Error: No filepath specified!');
				return;
			}
			var fileToOpen = new File(filepath);
			if (!fileToOpen.exists) {
				alert('Error: "' + filepath + '" doesn\'t exist!');
				return;
			}
			try { app.open(fileToOpen); }
			catch (e) {
				alert(e);
				return;
			}
		}
		else if (action == 'saveAs') {
			if (!serverID) {
				alert('Error: No server specified!');
				return;
			}
			var newFileBasename = '',
				classID, className, saveOptions, extension;

			if (assetID) {
				classID = assetID;
				className = 'ASSET';
				newFileBasename = assetName + '_' + taskFolder;
			}
			else if (shotID) {
				classID = shotID;
				className = 'SHOT';
				newFileBasename = shotName + '_' + taskFolder;
			}

			if (basenameListbox.selection)
				newFileBasename = basename;
			else if (tagInput.text)
				newFileBasename += '_' + tagInput.text.replace(/ /g, '_');
/*
			if (fileTypeDropdown.selection == 0) {
				saveOptions = new PhotoshopSaveOptions();
				extension = 'psd';
			}
			else if (fileTypeDropdown.selection == 1) {
				saveOptions = new EPSSaveOptions();
				extension = 'eps';
			}
			else if (fileTypeDropdown.selection == 2) {
				saveOptions = new GIFSaveOptions();
				extension = 'gif';
			}
			else if (fileTypeDropdown.selection == 3) {
				saveOptions = new JPEGSaveOptions();
				extension = 'jpg';
			}
			else if (fileTypeDropdown.selection == 4) {
				saveOptions = new PNGSaveOptions();
				extension = 'png';
			}
			else if (fileTypeDropdown.selection == 5) {
				saveOptions = new RawSaveOptions();
				extension = 'raw';
			}
			else if (fileTypeDropdown.selection == 6) {
				saveOptions = new TargaSaveOptions();
				extension = 'tga';
			}
			else if (fileTypeDropdown.selection == 7) {
				saveOptions = new TiffSaveOptions();
				extension = 'tif';
			}
*/

			saveOptions = new PhotoshopSaveOptions();
			extension = 'psd';

			var thisVersion = parseInt(maxVersion) + 1;

			if (saveFile(classID, className, serverID, serverPath, taskID, taskFolder, newFileBasename, commentInput.text, false, elementExports, saveOptions, extension, thisVersion))
				alert('Save successful.');
			else
				alert('Error: Save failed!');
		}
		/*
		else if (action == 'import') {
			if (!filepath) {
				alert('Error: No filepath specified!');
				return;
			}
			var fileToImport = new File(filepath);
			if (!fileToImport.exists) {
				alert('Error: "' + filepath + '" doesn\'t exist!');
				return;
			}
			try { app.project.importFile(new ImportOptions(fileToImport)); }
			catch (e) {
				alert(e);
				return;
			}
		}
		*/
		setPanelPrefs();
		nimPanel.close();
	}

	cancelButton.onClick = function() {
		setPanelPrefs();
		nimPanel.close();
	}

	// Set starting values based on NIM preferences file
	jobID = parseInt(getPref('Photoshop', 'jobID')) || 0;
	setInitialSelection('ID', jobID, jobs, jobDropdown);

	if (serverDropdown) {
		serverID = parseInt(getPref('Photoshop', 'serverID')) || 0;
		setInitialSelection('ID', serverID, servers, serverDropdown);
	}

	assetID = parseInt(getPref('Photoshop', 'assetID')) || 0;
	setInitialSelection('ID', assetID, assets, assetDropdown);

	showID = parseInt(getPref('Photoshop', 'showID')) || 0;
	setInitialSelection('ID', showID, shows, showDropdown);

	shotID = parseInt(getPref('Photoshop', 'shotID')) || 0;
	setInitialSelection('ID', shotID, shots, shotDropdown);
	if (shotID) jobTabPanel.selection = shotsTab;

	taskID = parseInt(getPref('Photoshop', 'taskID')) || 0;
	setInitialSelection('ID', taskID, tasks, taskDropdown);

	if (filterDropdown) {
		showPub = parseInt(getPref('Photoshop', 'showPub')) || 0;
		filterDropdown.selection = showPub;
		filterDropdown.onChange();
	}

	basename = getPref('Photoshop', 'basename');
	setInitialSelection('basename', basename, basenames, basenameListbox);

	nimPanel.show();
	return nimPanel;
}
