using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Nav;

public class OdomSubscriber : MonoBehaviour
{
    public Transform carTransform;
    ArticulationBody rootBody;
    ROSConnection ros;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<OdometryMsg>("/odom", UpdatePose);
        rootBody = carTransform.GetComponent<ArticulationBody>();
    }

    void UpdatePose(OdometryMsg msg)
    {
        double px = msg.pose.pose.position.x;
        double py = msg.pose.pose.position.y;
        double pz = msg.pose.pose.position.z;

        Vector3 newPos = new Vector3((float)-py, (float)pz, (float)px);

        double qx = msg.pose.pose.orientation.x;
        double qy = msg.pose.pose.orientation.y;
        double qz = msg.pose.pose.orientation.z;
        double qw = msg.pose.pose.orientation.w;

        Quaternion rosQuat = new Quaternion((float)qx, (float)qy, (float)qz, (float)qw);
        Vector3 euler = rosQuat.eulerAngles;
        Quaternion newRot = Quaternion.Euler(0, -euler.z, 0);

        if (rootBody != null)
        {
            rootBody.TeleportRoot(newPos, newRot);
        }
        else
        {
            carTransform.position = newPos;
            carTransform.rotation = newRot;
        }
    }
}
