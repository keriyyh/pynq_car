﻿using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityStandardAssets.Vehicles.Car;
using UnityEngine.UI; 

public class MenuHandler : MonoBehaviour {

	public GameObject PIDContoller;
	public GameObject Logger;
	public GameObject NetworkSteering;
	public GameObject menuPanel;
	public GameObject drivePanel;
    public GameObject carJSControl;
	public CameraFollow cameraFollow;
    public TrainingManager trainingManager;

    public void Awake()
    {
        //keep it processing even when not in focus.
        Application.runInBackground = true;

        //Set desired frame rate as high as possible.
        Application.targetFrameRate = 60;

        drivePanel.SetActive(false);
		cameraFollow = GameObject.FindObjectOfType<CameraFollow>();
    }

	public void OnStartDrive()
	{
		Logger.SetActive(false);
		menuPanel.SetActive(false);
		drivePanel.SetActive(true);
	}

	public void OnMainMenu(){
		if(PIDContoller != null)
			PIDContoller.SetActive(false);

		if(carJSControl != null)
			carJSControl.SetActive(false);

		NetworkSteering.SetActive(false);
		GameObject.Find("Record/Text").GetComponent<Text>().text = "Start Record";
		ifRecord = false;
		Logger.SetActive(false);
		menuPanel.SetActive(true);
		drivePanel.SetActive(false);
		cameraFollow.ifFollow = false;
	}
	public void OnPidDrive()
	{
		if(PIDContoller != null)
			PIDContoller.SetActive(true);

		if(carJSControl != null)
			carJSControl.SetActive(false);

		NetworkSteering.SetActive(false);
    }

	public void OnNNDrive()
	{
		if(PIDContoller != null)
			PIDContoller.SetActive(false);

		if(carJSControl != null)
			carJSControl.SetActive(false);

		NetworkSteering.SetActive(true);
    }

	public void OnHumanDrive()
	{
		if(PIDContoller != null)
			PIDContoller.SetActive(false);

		if(carJSControl != null)
			carJSControl.SetActive(true);

		NetworkSteering.SetActive(false);
    }

	bool ifRecord = false;
	public void OnRecord()
	{
		if(ifRecord){
			GameObject.Find("Record/Text").GetComponent<Text>().text = "Start Record";
			Logger.SetActive(false);
		}else{
			GameObject.Find("Record/Text").GetComponent<Text>().text = "Stop Record";
			Logger.SetActive(true);
		}
		ifRecord = !ifRecord;
    }

    public void OnNextTrack()
	{
		if(trainingManager != null)
			trainingManager.OnMenuNextTrack();
    }

	public void OnLoadPathScript(){
		if(trainingManager != null)
			trainingManager.OnMenuRegenTrack();
	}
    public void OnRandomTrack()
	{
		if(trainingManager != null)
			trainingManager.OnMenuRegenTrack();
    }
	public void OnCameraFollow()
	{
		cameraFollow.ifFollow = !cameraFollow.ifFollow;
	}
}
