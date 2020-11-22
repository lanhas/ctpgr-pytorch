import numpy as np
import torch

from torch.utils.data import DataLoader
import torch.optim as optim
from pathlib import Path
import visdom
from pafs_network import PAFsNetwork
from pafs_network import PAFsLoss
from aichallenger import AicNorm

class Trainer:
    def __init__(self, batch_size, debug_mode):
        # self.debug_mode:
        #    Set num_worker to 0. Otherwise pycharm debug won't work due to multithreading.
        #    Set batch_size to 1, ignore the argument given.
        self.debug_mode = debug_mode
        self.epochs = 100
        self.val_step = 500
        self.vis = visdom.Visdom()

        if torch.cuda.is_available():
            print("GPU available.")
        else:
            print("GPU not available! running with CPU.")
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model_pose = PAFsNetwork(b1_classes=14, b2_classes=11)
        self.model_pose.to(self.device, dtype=torch.float)

        self.model_optimizer = optim.Adam(self.model_pose.parameters(), lr=1e-3)
        self.model_path = Path("pose_model.pt")
        self.loss_model = PAFsLoss()

        if self.debug_mode:
            self.batch_size = 1
            workers = 0
        else:
            self.batch_size = batch_size
            workers = 4

        train_dataset = AicNorm(Path.home() / "AI_challenger_keypoint", is_train=True,
                                resize_img_size=(512, 512), heat_size=(64, 64))
        self.train_loader = DataLoader(train_dataset, self.batch_size, shuffle=True, num_workers=workers,
                                       pin_memory=True, drop_last=True)

        test_dataset = AicNorm(Path.home() / "AI_challenger_keypoint", is_train=False,
                               resize_img_size=(512, 512), heat_size=(64, 64))
        self.val_loader = DataLoader(test_dataset, 1, shuffle=False, num_workers=workers, pin_memory=True,
                                     drop_last=True)
        self.val_iter = iter(self.val_loader)

    def set_train(self):
        """Convert models to training mode
        """
        self.model_pose.train()

    def set_eval(self):
        """Convert models to testing/evaluation mode
        """
        self.model_pose.eval()

    def train(self):
        self.epoch = 0
        self.step = 0
        self.load_model()
        for self.epoch in range(self.epochs):
            print("Epoch:{}".format(self.epoch))
            self.run_epoch()


    def run_epoch(self):

        self.set_train()
        for batch_idx, inputs in enumerate(self.train_loader):
            inputs["norm_aug_img"] = inputs["norm_aug_img"].to(self.device, dtype=torch.float)
            inputs["gau_vis"] = inputs["gau_vis"].to(self.device, dtype=torch.float)
            inputs["pafs"] = inputs["pafs"].to(self.device, dtype=torch.float)
            loss, _, _ = self.process_batch(inputs)
            self.model_optimizer.zero_grad()
            loss.backward()
            self.model_optimizer.step()
            if self.step % self.val_step == 0:
                self.val()
                self.save_model()

            if self.step % 50 == 0:
                print("step {}; Loss {}".format(self.step, loss.item()))

            self.step += 1

    def val(self, ):
        """Validate the model on a single minibatch
        """
        self.set_eval()
        try:
            inputs = next(self.val_iter)
        except StopIteration:
            self.val_iter = next(self.val_iter)
            inputs = self.val_iter.next()

        inputs_gpu = {"norm_aug_img": inputs["norm_aug_img"].to(self.device, dtype=torch.float),
                      "gau_vis": inputs["gau_vis"].to(self.device, dtype=torch.float),
                      "pafs": inputs["pafs"].to(self.device, dtype=torch.float)}
        with torch.no_grad():
            loss, b1_out, b2_out = self.process_batch(inputs_gpu)
        pred_pcm_amax = np.amax(b1_out[0].cpu().numpy(), axis=0)  # HW
        gt_pcm_amax = np.amax(inputs["gau_vis"][0].cpu().numpy(), axis=0)
        pred_paf_amax = np.amax(b2_out[0].cpu().numpy(), axis=0)
        gt_paf_amax = np.amax(inputs["pafs"][0].cpu().numpy(), axis=0)

        self.vis.image(inputs["norm_aug_img"][0].cpu().numpy()[::-1, ...], win="Input", opts={'title': "Input"})
        self.vis.heatmap(pred_pcm_amax, win="Pred-PCM", opts={'title': "Pred-PCM"})
        self.vis.heatmap(gt_pcm_amax, win="GT-PCM", opts={'title': "GT-PCM"})
        self.vis.heatmap(pred_paf_amax, win="Pred-PAF", opts={'title': "Pred-PAF"})
        self.vis.heatmap(gt_paf_amax, win="GT-PAF", opts={'title': "GT-PAF"})
        self.vis.line(X=np.array([self.step]), Y=loss.cpu().numpy()[np.newaxis], win='Loss', update='append')
        self.set_train()

    def process_batch(self, inputs):
        """Pass a minibatch through the network and generate images and losses
        """
        b1_stages, b2_stages, b1_out, b2_out = self.model_pose(inputs["norm_aug_img"])
        gt_pcm = inputs["gau_vis"]  # ["heatmap"]: {"vis_or_not": NJHW, "visible": NJHW}
        gt_pcm = gt_pcm.unsqueeze(1)
        gt_paf = inputs["pafs"]
        gt_paf = gt_paf.unsqueeze(1)
        b1_stack = torch.stack(b1_stages, dim=1)  # Shape (N, Stage, C, H, W)
        b2_stack = torch.stack(b2_stages, dim=1)

        loss = self.loss_model(b1_stack, b2_stack, gt_pcm, gt_paf)

        return loss, b1_out, b2_out

    def save_model(self):

        torch.save(self.model_pose.state_dict(), self.model_path)
        print("Model saved.")

    def load_model(self):
        if Path.is_file(self.model_path):
            checkpoint = torch.load(self.model_path)
            self.model_pose.load_state_dict(checkpoint)
        else:
            print("No model file found.")


def main():
    Trainer(batch_size=5, debug_mode=True).train()


if __name__ == "__main__":
    main()
