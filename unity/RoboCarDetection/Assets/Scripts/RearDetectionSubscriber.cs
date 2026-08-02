using UnityEngine;
using TMPro;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

public class RearDetectionSubscriber : MonoBehaviour
{
    public TextMeshProUGUI rearDetectionText;
    ROSConnection ros;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<StringMsg>("/detections_json_rear", UpdateText);
    }

    void UpdateText(StringMsg msg)
    {
        string json = msg.data;
        if (json == "[]")
        {
            rearDetectionText.text = "Rear: No objects detected";
        }
        else
        {
            rearDetectionText.text = "Rear Detections:\n" + json;
        }
    }
}