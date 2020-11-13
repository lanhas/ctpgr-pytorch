from aichallenger.aic_augment import AicAugment
from pathlib import Path
import cv2
import numpy as np
from aichallenger.defination import Box, Joint, Person, Crowd
from typing import Tuple, List


class AicGaussian(AicAugment):
    """
    Provides gaussian heatmaps for keypoints, ranged 0~1
    """

    def __init__(self, data_path: Path, is_train: bool, resize_img_size: tuple, heat_size: tuple):
        super().__init__(data_path, is_train, resize_img_size)
        self.heat_size = heat_size
        self.__theta = 4
        self.__gaussian_generator = GaussianPoint(heat_size, self.__theta)

    def __getitem__(self, index) -> dict:
        res_dict = super().__getitem__(index)
        heat_dict = self.__gen_gaussian_for_image(res_dict["aug_label"])
        res_dict["gaussian"] = heat_dict
        return res_dict

    def __gen_gaussian_for_image(self, crowd: Crowd) -> dict:
        """
        为AIC数据集生成 gaussian heatmap
        :return:
        """

        def zero_heat():
            return np.zeros((self.heat_size[1], self.heat_size[0]), np.float)

        num_people: int = len(crowd)
        num_joints: int = len(crowd[0].joints)
        heat_dict = {"vis_or_not": [],
                     "visible": []}  # shape: (J,H,W). on_image: keypoint on image, visible or not visible
        for j in range(num_joints):
            # Heatmaps for same joint and different person
            heatmaps_vis_or_not = []  # Has heat when v=1,2, No heat when v=0 (not labeled)
            heatmaps_visible = []  # Has heat when v = 1, No heat when v=0,2 (not visible, labeled/unlabeled)
            for p in range(num_people):  # People
                cx, cy, v_value = crowd[p].joints[j]
                is_labeled = (v_value == 1 or v_value == 2)  # Vis or not
                is_visible = (v_value == 1)
                heatmap = self.__gaussian_generator.gen_heat_adjust_pt(self.resize_img_size, (cx, cy))

                heat_conf = heatmap if is_labeled else zero_heat()
                heat_vis = heatmap if is_visible else zero_heat()

                heatmaps_vis_or_not.append(heat_conf)
                heatmaps_visible.append(heat_vis)
            # Heatmap of same joints and different people
            heat_people_vis_not = np.amax(heatmaps_vis_or_not, axis=0)
            heat_people_vis = np.amax(heatmaps_visible, axis=0)
            heat_dict["vis_or_not"].append(heat_people_vis_not)
            heat_dict["visible"].append(heat_people_vis)

        return heat_dict

    # def __show_gaussian_map(self, img, heat):
    #     conf_gray_map = np.amax(heat["vis_or_not"], axis=0)
    #     vis_gray_map = np.amax(heat["visible"], axis=0)
    #
    #     plt.close('all')
    #     fig, ax = plt.subplots(2, 2)
    #     img = np.asarray(img)
    #     ax[0][0].imshow(img)
    #     ax[1][0].imshow(conf_gray_map)
    #     ax[1][1].imshow(vis_gray_map)
    #     plt.show()
    #     plt.pause(10)


# Generate a Gaussian point on black image.
class GaussianPoint:

    def __init__(self, heat_size, theta):
        self.w = heat_size[0]  # Heat w
        self.h = heat_size[1]
        self.theta = theta

    def gen_heat(self, pt):
        """
        Args:
            pt: a coordinate (x,y)
        """
        cx, cy = pt[0], pt[1]
        x_mesh, y_mesh = np.meshgrid(np.arange(0, self.w), np.arange(0, self.h))
        heatmap = np.exp(-(np.square(x_mesh - cx) + np.square(y_mesh - cy)) / (np.square(self.theta)))
        heatmap = heatmap.astype(np.float)
        return heatmap

    def gen_heat_adjust_pt(self, img_size, pt):
        """
        When image size not equal to heat size, this function adjust image keypoints to heat keypoints
        :param img_size:
        :return:
        """
        img_w, img_h = img_size
        ratio_w = self.w / img_w
        ratio_h = self.h / img_h
        heat_x = pt[0] * ratio_w
        heat_y = pt[1] * ratio_h
        heatmap = self.gen_heat((heat_x, heat_y))
        return heatmap
