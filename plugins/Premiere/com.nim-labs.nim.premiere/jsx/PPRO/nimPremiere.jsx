#include "PPro_API_Constants.jsx"

if(typeof JSON!=='object'){JSON={};}(function(){'use strict';function f(n){return n<10?'0'+n:n;}if(typeof Date.prototype.toJSON!=='function'){Date.prototype.toJSON=function(){return isFinite(this.valueOf())?this.getUTCFullYear()+'-'+f(this.getUTCMonth()+1)+'-'+f(this.getUTCDate())+'T'+f(this.getUTCHours())+':'+f(this.getUTCMinutes())+':'+f(this.getUTCSeconds())+'Z':null;};String.prototype.toJSON=Number.prototype.toJSON=Boolean.prototype.toJSON=function(){return this.valueOf();};}var cx,escapable,gap,indent,meta,rep;function quote(string){escapable.lastIndex=0;return escapable.test(string)?'"'+string.replace(escapable,function(a){var c=meta[a];return typeof c==='string'?c:'\\u'+('0000'+a.charCodeAt(0).toString(16)).slice(-4);})+'"':'"'+string+'"';}function str(key,holder){var i,k,v,length,mind=gap,partial,value=holder[key];if(value&&typeof value==='object'&&typeof value.toJSON==='function'){value=value.toJSON(key);}if(typeof rep==='function'){value=rep.call(holder,key,value);}switch(typeof value){case'string':return quote(value);case'number':return isFinite(value)?String(value):'null';case'boolean':case'null':return String(value);case'object':if(!value){return'null';}gap+=indent;partial=[];if(Object.prototype.toString.apply(value)==='[object Array]'){length=value.length;for(i=0;i<length;i+=1){partial[i]=str(i,value)||'null';}v=partial.length===0?'[]':gap?'[\n'+gap+partial.join(',\n'+gap)+'\n'+mind+']':'['+partial.join(',')+']';gap=mind;return v;}if(rep&&typeof rep==='object'){length=rep.length;for(i=0;i<length;i+=1){if(typeof rep[i]==='string'){k=rep[i];v=str(k,value);if(v){partial.push(quote(k)+(gap?': ':':')+v);}}}}else{for(k in value){if(Object.prototype.hasOwnProperty.call(value,k)){v=str(k,value);if(v){partial.push(quote(k)+(gap?': ':':')+v);}}}}v=partial.length===0?'{}':gap?'{\n'+gap+partial.join(',\n'+gap)+'\n'+mind+'}':'{'+partial.join(',')+'}';gap=mind;return v;}}if(typeof JSON.stringify!=='function'){escapable=/[\\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g;meta={'\b':'\\b','\t':'\\t','\n':'\\n','\f':'\\f','\r':'\\r','"':'\\"','\\':'\\\\'};JSON.stringify=function(value,replacer,space){var i;gap='';indent='';if(typeof space==='number'){for(i=0;i<space;i+=1){indent+=' ';}}else if(typeof space==='string'){indent=space;}rep=replacer;if(replacer&&typeof replacer!=='function'&&(typeof replacer!=='object'||typeof replacer.length!=='number')){throw new Error('JSON.stringify');}return str('',{'':value});};}if(typeof JSON.parse!=='function'){cx=/[\u0000\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g;JSON.parse=function(text,reviver){var j;function walk(holder,key){var k,v,value=holder[key];if(value&&typeof value==='object'){for(k in value){if(Object.prototype.hasOwnProperty.call(value,k)){v=walk(value,k);if(v!==undefined){value[k]=v;}else{delete value[k];}}}}return reviver.call(holder,key,value);}text=String(text);cx.lastIndex=0;if(cx.test(text)){text=text.replace(cx,function(a){return'\\u'+('0000'+a.charCodeAt(0).toString(16)).slice(-4);});}if(/^[\],:{}\s]*$/.test(text.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g,'@').replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g,']').replace(/(?:^|:|,)(?:\s*\[)+/g,''))){j=eval('('+text+')');return typeof reviver==='function'?walk({'':j},''):j;}throw new SyntaxError('JSON.parse');};}}());;  

$._nim_PPP_={
	
	debug : false,
	exportJobs : {},
	
	getProjectPath: function(){
		return app.project.path;
	},

	getActiveSequenceName : function(){
		return app.project.activeSequence.name;
	},

	selectFileDialog : function(dlgTitle,filterString){
		filter = 0;
		if(filterString){
			filter = filterString;
		}
		var selectedFile = File.openDialog (dlgTitle, filter, false);
		var fsName = '';
		if(selectedFile){
			fsName = selectedFile.fsName;
		}
		return fsName;
	},

	selectFolderDialog : function(){
		var outFolder = Folder.selectDialog();
		var fsName = '';
		if(outFolder){
			fsName = outFolder.fsName;
		}
		return fsName;
	},

	getProjectMetadata : function(data){
		data = JSON.parse(data);
		if (app.isDocumentOpen()) {
			//var projectItem = app.project.activeSequence.projectItem;
			var projectItem	= app.project.rootItem.children[0]; // just grabs first projectItem.
			if (projectItem) {
				if (ExternalObject.AdobeXMPScript === undefined) {
					ExternalObject.AdobeXMPScript = new ExternalObject('lib:AdobeXMPScript');
				}
				if (ExternalObject.AdobeXMPScript !== undefined) {
					var kPProPrivateProjectMetadataURI	= "http://ns.adobe.com/premierePrivateProjectMetaData/1.0/";
					var projectMetadata	= projectItem.getProjectMetadata();
					var xmp	= new XMPMeta(projectMetadata);

					for (var key in data) {
						$._nim_PPP_.debugLog('Reading Property: '+key);
						if(xmp.doesPropertyExist(kPProPrivateProjectMetadataURI, key)){
							var property = xmp.getProperty(kPProPrivateProjectMetadataURI, key);
							$._nim_PPP_.debugLog('Property Found: '+property.value);
							data[key] = property.value;
							data[key] = data[key] == " " ? "" : data[key];
						}
						$._nim_PPP_.debugLog('--------------------------------------');
					}

					data["nim_pproProjectPath"] = app.project.path;
					return JSON.stringify(data);
				}
			}
		}
		return false;
	},

	setProjectMetadata : function(data) {
		$._nim_PPP_.debugLog('setProjectMetadata: '+data);
		data = JSON.parse(data);

		if (app.isDocumentOpen()) {
			//var projectItem = app.project.activeSequence.projectItem;
			var projectItem	= app.project.rootItem.children[0]; // just grabs first projectItem.
			if (projectItem) {
				if (ExternalObject.AdobeXMPScript === undefined) {
					ExternalObject.AdobeXMPScript = new ExternalObject('lib:AdobeXMPScript');
				}
				if (ExternalObject.AdobeXMPScript !== undefined) {
					var kPProPrivateProjectMetadataURI	= "http://ns.adobe.com/premierePrivateProjectMetaData/1.0/";
					var projectMetadata	= projectItem.getProjectMetadata();
					var xmp	= new XMPMeta(projectMetadata);

					var fieldArray	= [];

					// Define Project Properties
					for( var key in data){
						if( data[key] !== undefined ){
							if (xmp.doesPropertyExist(kPProPrivateProjectMetadataURI, key)){
								$._nim_PPP_.debugLog('Property Found: '+key);
								$._nim_PPP_.debugLog('Property Data: '+data[key]);
								$._nim_PPP_.debugLog('Property Type: '+typeof data[key]);
								data[key] = data[key] == "" ? " " : data[key];
								xmp.setProperty(kPProPrivateProjectMetadataURI, key, data[key]);
								$._nim_PPP_.debugLog('Property Set: '+key);
							}
							else{
								var successfullyAdded = app.project.addPropertyToProjectMetadataSchema(key, key, 2);
								$._nim_PPP_.debugLog('Adding Property: '+key);
								if(successfullyAdded){
									$._nim_PPP_.debugLog('Property Added');
									data[key] = data[key] == "" ? " " : data[key];
									xmp.setProperty(kPProPrivateProjectMetadataURI, key, data[key]);
									$._nim_PPP_.debugLog('Property Set: '+key+ ' : '+data[key]);
								}
								else {
									$._nim_PPP_.debugLog('Failed to Add Property: '+key);
								}
							}
							$._nim_PPP_.debugLog('--------------------------------------');
							fieldArray.push(key);
						}
					}
					$._nim_PPP_.debugLog('FieldArray: '+JSON.stringify(fieldArray));

					var str = xmp.serialize();
					projectItem.setProjectMetadata(str, fieldArray);
					return true;
				}
			}
		}
		return false;
	},

	projectOpen : function(projToOpen) {
		$._nim_PPP_.debugLog('projectOpen - projToOpen: ' + projToOpen);
		if (projToOpen) {
			var result = app.openDocument(	projToOpen,
											1,					// suppress 'Convert Project' dialogs
											1,					// suppress 'Locate Files' dialogs
											1);					// suppress warning dialogs
			$._nim_PPP_.debugLog('projectOpen - result: ' + JSON.stringify(result));
		}	
		else {
			alert("Project Not Found");
		}
	},

	projectSaveAs : function(projToSave) {
		$._nim_PPP_.debugLog('projectSaveAs - projToSave: ' + projToSave);
		if (projToSave) {
			var result = app.project.saveAs( projToSave );
			$._nim_PPP_.debugLog('projectSaveAs - result: ' + JSON.stringify(result));
		}	
		else {
			alert("Project Not Found");
		}
	},

	projectPublish : function() {
		var ogPath = app.project.path;
		var ogPathWithoutExt = ogPath.substr(0, ogPath.length - 7);
		var projToPub = ogPathWithoutExt+'_PUB'+'.prproj';
		app.project.saveAs(projToPub);

		for (var a = 0; a < app.projects.numProjects; a++){ 
			var currentProject = app.projects[a]; 
			if (currentProject.path === projToPub){ 
				app.openDocument(ogPath);
				currentProject.closeDocument(); 
			} 
		}
	},

	exportEdit : function(context, itemID, name, desc, typeID, statusID, keywords, preset, presetPath, range, diskID, disk, keep, markers) {

		app.encoder.bind('onEncoderJobComplete',	$._nim_PPP_.onEncoderJobComplete);
		app.encoder.bind('onEncoderJobError', 		$._nim_PPP_.onEncoderJobError);
		app.encoder.bind('onEncoderJobProgress', 	$._nim_PPP_.onEncoderJobProgress);
		app.encoder.bind('onEncoderJobQueued', 		$._nim_PPP_.onEncoderJobQueued);
		app.encoder.bind('onEncoderJobCanceled',	$._nim_PPP_.onEncoderJobCanceled);

		var activeSequence = app.project.activeSequence;
		var sequenceID = activeSequence.sequenceID;
		var sequenceName = activeSequence.name;
		var outputPath = sequenceName+'.mov';
		
		var projectPath = app.project.path;
		var pathArray = projectPath.split(/[\\\/]/);
		var basename = pathArray.pop();
		projectPath = projectPath.substring(0,projectPath.indexOf(basename));

		if(diskID == 0){
			outputPath = projectPath+outputPath;
		}
		if(diskID == 1){
			outputPath = disk+outputPath;
		}
		if(diskID == 2){
			outputPath = disk+outputPath;
		}

		$._nim_PPP_.debugLog('exportEdit - outputPath:' + outputPath);
		$._nim_PPP_.debugLog('exportEdit - presetPath:' + presetPath);
		$._nim_PPP_.debugLog('exportEdit - range:' + range);

		var workArea = parseInt(range);
		var removeOnComplete = 1;

		// Attach marker info
		var markerData = [];
		if(markers == 1){
			markerData = activeSequence.markers;

			var numMarkers	= markerData.numMarkers;
			if (numMarkers > 0) {
				var m = 0;
				for(var current_marker	=	markerData.getFirstMarker();
						current_marker	!==	undefined; 
						current_marker 	=	markerData.getNextMarker(current_marker)){

					$._nim_PPP_.debugLog('exportEdit - marker.name:' + current_marker.name);
					$._nim_PPP_.debugLog('exportEdit - marker.comments:' + current_marker.comments);
					
					var markerItem = { name : current_marker.name,
									   comments: current_marker.comments,
									   type : current_marker.type,
									   start : current_marker.start,
									   end : current_marker.end };
					markerData[m] = (markerItem);
					m = m + 1;
				}    
			}
		}

		var encodeJobID = app.encoder.encodeSequence(activeSequence, outputPath, presetPath, workArea, removeOnComplete);

		$._nim_PPP_.exportJobs[encodeJobID] = { encode : "sequence", jobID : encodeJobID, sequenceID : sequenceID, context : context, 
												itemID : itemID, name : name, desc : desc, typeID : typeID, statusID : statusID, 
												keywords : keywords, preset : preset, presetPath : presetPath, range : range, 
												diskID : diskID, disk : disk, keep : keep, markers : markers, markerData: markerData };

		return JSON.stringify($._nim_PPP_.exportJobs[encodeJobID]);
	},

	exportClip : function(trackID, clipID, itemID, name, typeID, preset, presetPath, outputPath, length, handles) {

		app.encoder.bind('onEncoderJobComplete',	$._nim_PPP_.onEncoderJobComplete);
		app.encoder.bind('onEncoderJobError', 		$._nim_PPP_.onEncoderJobError);
		app.encoder.bind('onEncoderJobProgress', 	$._nim_PPP_.onEncoderJobProgress);
		app.encoder.bind('onEncoderJobQueued', 		$._nim_PPP_.onEncoderJobQueued);
		app.encoder.bind('onEncoderJobCanceled',	$._nim_PPP_.onEncoderJobCanceled);

		$._nim_PPP_.debugLog('exportEdit - trackID:' + trackID);
		$._nim_PPP_.debugLog('exportEdit - clipID:' + clipID);
		$._nim_PPP_.debugLog('exportEdit - itemID:' + itemID);
		$._nim_PPP_.debugLog('exportEdit - name:' + name);
		$._nim_PPP_.debugLog('exportEdit - typeID:' + typeID);
		$._nim_PPP_.debugLog('exportEdit - preset:' + preset);
		$._nim_PPP_.debugLog('exportEdit - presetPath:' + presetPath);
		$._nim_PPP_.debugLog('exportEdit - outputPath:' + outputPath);
		$._nim_PPP_.debugLog('exportEdit - length:' + length);
		$._nim_PPP_.debugLog('exportEdit - handles:' + handles);

		

		var clip = app.project.activeSequence.videoTracks[trackID].clips[clipID];
		var projectItem = clip.projectItem;

		var workArea = 0;
		var removeOnComplete = 1;
		
		

		if(length == "0"){	// CUT + HANDLES

			// May need to test for projectItem type
			//$._nim_PPP_.message("projectItem.type: "+projectItem.type);

			var ticksPerSecond = 254016000000; 							// Ticks per second
			var ticksPerFrame = app.project.activeSequence.timebase; 	// Ticks per frame
			//var framerate = ticksPerSecond/ticksPerFrame;
			
			var inPoint = clip.inPoint.seconds - ((parseInt(handles) * ticksPerFrame)/ticksPerSecond);		// Convert handles from frames to seconds
			inPoint = inPoint < 0 ? 0 : inPoint; // Keep from going negative

			var outPoint = clip.outPoint.seconds + ((parseInt(handles) * ticksPerFrame)/ticksPerSecond);	// Convert handles from frames to seconds
			
			var mediaFile = projectItem.getMediaPath();

			if(mediaFile !== undefined){
				var encodeJobID = app.encoder.encodeFile(mediaFile, outputPath, presetPath, removeOnComplete, inPoint, outPoint);

				$._nim_PPP_.exportJobs[encodeJobID] = { encode : "clip", jobID : encodeJobID, trackID : trackID, clipID : clipID, itemID : itemID, 
														name : name, typeID : typeID, preset : preset, presetPath : presetPath, outputPath : outputPath,
														length : length, handles : handles };

				return JSON.stringify($._nim_PPP_.exportJobs[encodeJobID]);
			}
		}
		else if(length == "1"){ // SOURCE CLIP
			var encodeJobID = app.encoder.encodeProjectItem(projectItem, outputPath, presetPath, workArea, removeOnComplete);

			$._nim_PPP_.exportJobs[encodeJobID] = { encode : "clip", jobID : encodeJobID, trackID : trackID, clipID : clipID, itemID : itemID, 
													name : name, typeID : typeID, preset : preset, presetPath : presetPath, outputPath : outputPath,
													length : length, handles : handles };

			return JSON.stringify($._nim_PPP_.exportJobs[encodeJobID]);
		}
		
		return "false";
	},

	getSequenceItems : function (rename, nameTemplate, layerOption){
		// Retrives all video trackItems in a sequence
		// optionally renames clips based on nameTemplate

		$._nim_PPP_.debugLog('getSequenceItems');

		var sequenceObj = {};

		var activeSequence = app.project.activeSequence;
		sequenceObj['sequenceID'] = activeSequence.sequenceID;
		sequenceObj['sequenceName'] = activeSequence.name;

		var videoTracks = activeSequence.videoTracks;
		$._nim_PPP_.debugLog('videoTracks: '+JSON.stringify(videoTracks));

		var tracks = [];
		var firstTrack = true;
		for(var i=0; i<videoTracks.numTracks; i++){
			var trackInfo = {};
			trackInfo['name'] = videoTracks[i].name;
			trackInfo['ID'] = videoTracks[i].id;
			trackInfo['mediaType'] = videoTracks[i].mediaType;

			var trackClips = videoTracks[i].clips;
			$._nim_PPP_.debugLog('trackClips: '+JSON.stringify(trackClips));

			var clips = [];
			for(var j=0; j<trackClips.numItems; j++){
				var clipInfo = {};

				// Use first track as basis for rename (should be first track with clips if track 0 is empty)
				if(rename == "1"){
					if(firstTrack==true){
						trackClips[j].name = $._nim_PPP_.renameClip(nameTemplate,j);
						$._nim_PPP_.debugLog("renameClip: "+trackClips[j].name);
					}
					else{
						trackClips[j].name = $._nim_PPP_.getVerticalTrackName(trackClips[j], i, layerOption);
						$._nim_PPP_.debugLog("getVerticalTrackName: "+trackClips[j].name);
					}
				}
				clipInfo['name'] = trackClips[j].name;
				clipInfo['duration'] = trackClips[j].duration;
				clipInfo['start'] = trackClips[j].start;
				clipInfo['end'] = trackClips[j].end;
				clipInfo['inPoint'] = trackClips[j].inPoint;
				clipInfo['outPoint'] = trackClips[j].outPoint;
				clipInfo['mediaType'] = trackClips[j].mediaType;
				clipInfo['projectItem'] = trackClips[j].projectItem;
				clips.push(clipInfo);	
			}
			if(trackClips.numItems >  0){
				firstTrack = false;
			}
			trackInfo['clips'] = clips;
			tracks.push(trackInfo);
			
		}
		sequenceObj['tracks'] = tracks;

		return JSON.stringify(sequenceObj);
	},

	renameClip : function(nameTemplate, clipIndex){
		var frameReg = /^([^\<\>]*)<(#*)(?:x(\d*))?(?:@(\d*))?>(.*)$/g;
		var frameItems = frameReg.exec(nameTemplate);
		var prefix = frameItems[1] !== undefined ? frameItems[1] : "";
		var padding = frameItems[2] !== undefined ? (frameItems[2].match(/#/g) || []).length : 0;
		var skip = frameItems[3] !== undefined ? parseInt(frameItems[3]) : 1;
		skip = skip <= 0 ? 1 : skip;	// Skip must be at least 1
		var start = frameItems[4] !== undefined ? parseInt(frameItems[4]) : 0;
		var suffix = frameItems[5] !== undefined ? frameItems[5] : "";
		var number = ((clipIndex*skip)+start).toString();
        
        number = $._nim_PPP_.padNumber(number, padding);
        var shotName = prefix+number+suffix;
		return shotName;
	},

	exportClipIcon : function(clip) {
		$._nim_PPP_.debugLog('clip: '+clip);
		clip = JSON.parse(clip);

		$._nim_PPP_.setPlayerPosition(clip.start.ticks);
		var outputFileName = $._nim_PPP_.exportCurrentFrameAsPNG();
		clip["outputFileName"] = outputFileName;

		return JSON.stringify(clip);
	},

	getVerticalTrackName : function(clip, trackNumber, layerOption){
		var inClipStartTicks = parseInt(clip.start.ticks);
		var inClipEndTicks = parseInt(clip.end.ticks);
		$._nim_PPP_.debugLog("inClipStartTicks: "+inClipStartTicks);
		$._nim_PPP_.debugLog("inClipEndTicks: "+inClipEndTicks);

		var activeSequence = app.project.activeSequence;
		var videoTracks = activeSequence.videoTracks;
		var clipName = "";
		
		// TODO:  Build array and count number of lower items, optionally append suffix based on track (ie SH001A)
		trackLoop:
		for(var i=0; i<trackNumber; i++){
			var trackClips = videoTracks[i].clips;
			
			for(var j=0; j<trackClips.numItems; j++){
				$._nim_PPP_.debugLog("trackClip name: "+trackClips[j].name);
				var clipStartTicks = parseInt(trackClips[j].start.ticks);
				var clipEndTicks =parseInt( trackClips[j].end.ticks);

				$._nim_PPP_.debugLog("clipStartTicks: "+clipStartTicks);
				$._nim_PPP_.debugLog("clipEndTicks: "+clipEndTicks);

				if(layerOption == 0){	// Match First Frame
					if(clipStartTicks <= inClipStartTicks && clipEndTicks > inClipStartTicks){
						$._nim_PPP_.debugLog("Match Found: "+trackClips[j].name);
						clipName = trackClips[j].name;
						break trackLoop;
					}
				}
				else {	// Match End Frame
					if(clipStartTicks < inClipEndTicks && clipEndTicks >= inClipEndTicks){
						$._nim_PPP_.debugLog("Match Found: "+trackClips[j].name);
						clipName = trackClips[j].name;
						break trackLoop;
					}
				}
			}
		}

		$._nim_PPP_.debugLog("clipName: "+clipName);

		if(clipName == ""){
			clipName = clip.name;
		}

		return clipName;
	},

	setPlayerPosition : function(ticks) {
		var activeSequence = app.project.activeSequence;
		activeSequence.setPlayerPosition(ticks);
	},

	exportCurrentFrameAsPNG : function() {
		app.enableQE();
		var activeSequence	= qe.project.getActiveSequence(); 	// note: make sure a sequence is active in PPro UI
		if (activeSequence) {
			// Create a file name based on timecode of frame.
			var time			= activeSequence.CTI.timecode; 	// CTI = Current Time Indicator.
			var removeThese 	= /:|;/ig;    // Why? Because Windows chokes on colons.
			var timeName = time.replace(removeThese, '_');
			var outputPath		= new File("~/.nim/tmp");
			var outputName 		= activeSequence.name+"_"+timeName+"_"+$._nim_PPP_.guid();
			outputName = outputName.replace(/\ /g,'_');

			var outputFileName	= outputPath.fsName + $._nim_PPP_.getSep() + outputName;
			activeSequence.exportFramePNG(time, outputFileName);
			outputFileName += ".png";
			return outputFileName;
		} else {
			$._nim_PPP_.message("No active sequence.");
		}
		return false;
	},

	importElements : function(shotTree, destination, binName) {
		$._nim_PPP_.debugLog("importElements");
		var result = false;

		if (app.project) {
			var binMade = false;
			var projectRootItem = app.project.rootItem;
			var nimBin = projectRootItem;
			if(destination == "1"){
				nimBin = app.project.getInsertionBin();
			}
			if(destination == "2"){
				// Create NIM Root Bin
				nimBin = $._nim_PPP_.findBin(projectRootItem, binName);
				if(nimBin === false){
					binMade = projectRootItem.createBin("NIM Elements");
					nimBin = $._nim_PPP_.findBin(projectRootItem, binName);
				}
			}

			shotTree = JSON.parse(shotTree);
			if (shotTree) 
			{
				for(var i=0; i<shotTree.length; i++){
					var shotData = shotTree[i];
					var shotName = shotData['shotName'];

					var shotBin = $._nim_PPP_.findBin(nimBin, shotName);
					if(shotBin === false){
						binMade = nimBin.createBin(shotName);
						shotBin = $._nim_PPP_.findBin(nimBin, shotName);
					}
					
					if(shotBin !== false){
						var elementFiles = [];
						for(var j=0;j<shotData['elements'].length; j++){
							var element = shotData['elements'][j];
							var elementPath = element['full_path'];
							var elementName = element['name'];

							// Check for existing element in project and skip if found
							var fileFound = $._nim_PPP_.findFile(nimBin, elementName);
							if(fileFound === false){
								elementFiles.push(elementPath);
							}
						}
						if(elementFiles){
							result = app.project.importFiles(elementFiles, 
													0,								// suppress warnings 
													shotBin, 						// app.project.getInsertionBin(),  // - projectItem
													1);								// import as numbered stills	
						}
					}
					
				}
			} 
			else {
				$._nim_PPP_.message("No files to import.");
				result = false;
			} 
		}
		return JSON.stringify(result);
	},

	findBin : function(rootBin, binName) {
		var binFound = false;
		var bin = null;
		if (app.project) {
			var projectChildren = rootBin.children;
			for(var i=0; i<projectChildren.numItems; i++){
				var projectChild = projectChildren[i];
				if(projectChild.type == 2){				// 'BIN'
					if(projectChild.name == binName){
						binFound = true;
						bin = projectChild;
						break;
					}
					else {
						var childFound = $._nim_PPP_.findBin(projectChild, binName);
						if( childFound !== false ){
							binFound = true;
							bin = projectChild;
							break;
						}
					}
				}
			}
		}
		if(binFound){
			return bin;
		}
		else {
			return false;
		}
	},

	findFile : function(rootBin, fileName) {
		var fileFound = false;
		var fileItem = null;
		if (app.project) {
			var projectChildren = rootBin.children;
			for(var i=0; i<projectChildren.numItems; i++){
				var projectChild = projectChildren[i];
				if(projectChild.type == 1 || projectChild.type == 4){				// 'CLIP' or 'FILE'
					if(projectChild.name == fileName){
						fileFound = true;
						fileItem = projectChild;
						break;
					}
				}
				else if(projectChild.type == 2) {		// 'BIN'
					var childFound = $._nim_PPP_.findFile(projectChild, fileName);
					if( childFound !== false ){
						fileFound = true;
						fileItem = projectChild;
						break;
					}
				}
			}
		}
		if(fileFound){
			return fileItem;
		}
		else {
			return false;
		}
	},

	// Callbacks
	guid : function() {
		function s4() {
			return Math.floor((1 + Math.random()) * 0x10000)
			.toString(16)
			.substring(1);
		}
		//return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
		return s4() + s4() + s4() + s4() + s4() + s4() + s4() + s4();
	},

	padNumber : function( number, padding) {
		var width = padding - number.length;
		if(width > 0){
			for(var i=0;i<width;i++){
				number = "0"+number;
			}
		}
		return number;
	},

	getSep : function() {
		if (Folder.fs == 'Macintosh') {
			return '/';
		} else {
			return '\\';
		}
	},

	message : function (msg) {
		// Using '$' object will invoke ExtendScript Toolkit, if installed.
		$.writeln(msg);	 
	},

	debugLog : function (msg) {
		if($._nim_PPP_.debug){
			$.writeln(msg);	 // Using '$' object will invoke ExtendScript Toolkit, if installed.
		}
	},

	onEncoderJobComplete : function (jobID, outputFilePath) {
		var eoName;
		if (Folder.fs == 'Macintosh') {
			eoName = "PlugPlugExternalObject";							
		} else {
			eoName = "PlugPlugExternalObject.dll";
		}
		var mylib = new ExternalObject('lib:' + eoName);
				
		var jobData = $._nim_PPP_.exportJobs[jobID];
		jobData['outputFilePath'] = outputFilePath;
		delete $._nim_PPP_.exportJobs[jobID];

		var nimEvent = new CSXSEvent();
		nimEvent.type = "com.nim-labs.events.PProExportEditComplete";
		nimEvent.data = JSON.stringify(jobData);
		nimEvent.dispatch();
	},

	onEncoderJobError : function (jobID, errorMessage) {
		var eoName; 

		if (Folder.fs === 'Macintosh') {
			eoName	= "PlugPlugExternalObject";							
		} else {
			eoName	= "PlugPlugExternalObject.dll";
		}
				
		var mylib		= new ExternalObject('lib:' + eoName);
		var eventObj	= new CSXSEvent();

		eventObj.type	= "com.nim-labs.events.PProExportEditError";
		eventObj.data	= "Job " + jobID + " failed, due to " + errorMessage + ".";
		eventObj.dispatch();
	},
	
	onEncoderJobProgress : function (jobID, progress) {
		$._nim_PPP_.debugLog('onEncoderJobProgress called. jobID = ' + jobID + '. progress = ' + progress + '.');

		var eoName;
		if (Folder.fs == 'Macintosh') {
			eoName = "PlugPlugExternalObject";							
		} else {
			eoName = "PlugPlugExternalObject.dll";
		}
		var mylib = new ExternalObject('lib:' + eoName);
		
		var jobData = $._nim_PPP_.exportJobs[jobID];

		var jobProgress = { jobID: jobID, progress: progress, encode: jobData["encode"], itemID: jobData["itemID"] };
		var nimEvent = new CSXSEvent();
		nimEvent.type = "com.nim-labs.events.PProExportEditProgress";
		nimEvent.data = JSON.stringify(jobProgress);
		nimEvent.dispatch();
	},

	onEncoderJobQueued : function (jobID) {

		var eoName;
		if (Folder.fs == 'Macintosh') {
			eoName = "PlugPlugExternalObject";							
		} else {
			eoName = "PlugPlugExternalObject.dll";
		}
		var mylib = new ExternalObject('lib:' + eoName);
		
		//$._nim_PPP_.exportJobs[jobID]['jobID'] = jobID;
		var jobData = $._nim_PPP_.exportJobs[jobID];

		var nimEvent = new CSXSEvent();
		nimEvent.type = "com.nim-labs.events.PProExportEditQueued";
		nimEvent.data = JSON.stringify(jobData);
		nimEvent.dispatch();

		app.encoder.startBatch();
	},

	onEncoderJobCanceled : function (jobID) {
		$._nim_PPP_.debugLog('OnEncoderJobCanceled called. jobID = ' + jobID +  '.');
	},

};
