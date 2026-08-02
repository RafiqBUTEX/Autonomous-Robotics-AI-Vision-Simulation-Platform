using UnityEngine;
using UnityEngine.UI;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Geometry;

public class CarController : MonoBehaviour
{
    public Slider linearSlider;
    public Slider angularSlider;

    ROSConnection ros;
    float publishRate = 10f;
    float timer = 0f;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<TwistMsg>("/cmd_vel");
    }

    void Update()
    {
        timer += Time.deltaTime;
        if (timer >= 1f / publishRate)
        {
            timer = 0f;
            PublishCmdVel();
        }
    }

    void PublishCmdVel()
    {
        TwistMsg twist = new TwistMsg();
        twist.linear.x = linearSlider.value;
        twist.angular.z = angularSlider.value;
        ros.Publish("/cmd_vel", twist);
    }
}