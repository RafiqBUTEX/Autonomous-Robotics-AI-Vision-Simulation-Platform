using UnityEngine;
using UnityEngine.UI;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Sensor;

public class CameraFeedSubscriber : MonoBehaviour
{
    public RawImage frontImage;
    public RawImage rearImage;

    Texture2D frontTex;
    Texture2D rearTex;
    ROSConnection ros;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<ImageMsg>("/camera/car_camera/image_raw", UpdateFront);
        ros.Subscribe<ImageMsg>("/camera/car_camera_rear/image_raw", UpdateRear);
    }

    void UpdateFront(ImageMsg msg)
    {
        frontTex = ConvertToTexture(msg, frontTex);
        frontImage.texture = frontTex;
    }

    void UpdateRear(ImageMsg msg)
    {
        rearTex = ConvertToTexture(msg, rearTex);
        rearImage.texture = rearTex;
    }

    Texture2D ConvertToTexture(ImageMsg msg, Texture2D tex)
    {
        int width = (int)msg.width;
        int height = (int)msg.height;

        if (tex == null || tex.width != width || tex.height != height)
        {
            tex = new Texture2D(width, height, TextureFormat.RGB24, false);
        }

        byte[] rgbData = new byte[width * height * 3];
        int rowSize = width * 3;
        for (int y = 0; y < height; y++)
        {
            int srcRow = y * rowSize;
            int dstRow = (height - 1 - y) * rowSize;
            for (int x = 0; x < width; x++)
            {
                int srcIdx = srcRow + x * 3;
                int dstIdx = dstRow + x * 3;
                rgbData[dstIdx] = msg.data[srcIdx + 2];
                rgbData[dstIdx + 1] = msg.data[srcIdx + 1];
                rgbData[dstIdx + 2] = msg.data[srcIdx];
            }
        }

        tex.LoadRawTextureData(rgbData);
        tex.Apply();
        return tex;
    }
}