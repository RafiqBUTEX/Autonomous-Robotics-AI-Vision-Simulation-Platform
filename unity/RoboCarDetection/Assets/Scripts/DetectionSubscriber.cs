using UnityEngine;
using TMPro;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

public class DetectionSubscriber : MonoBehaviour
{
    public TextMeshProUGUI detectionText;
    ROSConnection ros;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<StringMsg>("/detections_json", UpdateText);
    }

    void UpdateText(StringMsg msg)
    {
        string json = msg.data;
        if (json == "[]")
        {
            detectionText.text = "No objects detected";
        }
        else
        {
            detectionText.text = "Detections:\n" + json;
        }
    }
}