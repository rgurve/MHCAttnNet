import os
import time
import sys
import argparse
from tqdm import tqdm

from data_loader import get_dataset
from model import MHCAttnNet
import config

from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score, average_precision_score, f1_score
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

import matplotlib.pyplot as plt
import numpy as np

def fit(model, train_dl, val_dl, loss_fn, opt, epochs, device):
    num_batch = len(train_dl)
    scores = dict()
    scores['loss'] = list()
    scores['accuracy'] = list()
    scores['precision'] = list()
    scores['recall'] = list()
    scores['roc_auc'] = list()
    for epoch in range(1, epochs+1):
        print("Epoch", epoch)
        
        y_actual_train = list()
        y_pred_train = list()
        for row in tqdm(train_dl):
            if(row.batch_size == config.batch_size):
                y_pred = model(row.peptide, row.mhc_amino_acid)
                y_pred_idx = torch.max(y_pred, dim=1)[1]
                y_actual = row.bind
                y_actual_train += list(y_actual.cpu().data.numpy())
                y_pred_train += list(y_pred_idx.cpu().data.numpy())
                loss = loss_fn(y_pred, y_actual)
                opt.zero_grad()
                loss.backward()
                optimizer.step()
        accuracy = accuracy_score(y_actual_train, y_pred_train)
        precision = precision_score(y_actual_train, y_pred_train)
        recall = recall_score(y_actual_train, y_pred_train)
        f1 = f1_score(y_actual_train, y_pred_train)
        roc_auc = roc_auc_score(y_actual_train, y_pred_train)
        auc_rpc = average_precision_score(y_actual_train, y_pred_train)
        print(f"Train - Loss : {loss}, Accuracy : {accuracy}, Precision : {precision}, Recall : {recall}, F1-score : {f1}, ROC_AUC : {roc_auc}, AuRpC : {auc_rpc}")

        y_actual_val = list()
        y_pred_val = list()
        for row in tqdm(val_dl):
            if(row.batch_size == config.batch_size):
                y_pred = model(row.peptide, row.mhc_amino_acid)
                y_pred_idx = torch.max(y_pred, dim=1)[1]
                y_actual = row.bind
                y_actual_val += list(y_actual.cpu().data.numpy())
                y_pred_val += list(y_pred_idx.cpu().data.numpy())
                loss = loss_fn(y_pred, y_actual)            
        accuracy = accuracy_score(y_actual_val, y_pred_val)
        precision = precision_score(y_actual_val, y_pred_val)
        recall = recall_score(y_actual_val, y_pred_val)
        f1 = f1_score(y_actual_val, y_pred_val)
        roc_auc = roc_auc_score(y_actual_val, y_pred_val)
        auc_rpc = average_precision_score(y_actual_val, y_pred_val)
        print(f"Validation - Loss : {loss}, Accuracy : {accuracy}, Precision : {precision}, Recall : {recall}, F1-score : {f1}, ROC_AUC : {roc_auc}, AuRpC : {auc_rpc}")

        scores['loss'].append(loss)
        scores['accuracy'].append(accuracy)
        scores['precision'].append(precision)
        scores['recall'].append(recall)
        scores['roc_auc'].append(roc_auc)

        if(epoch%2 == 0):
            torch.save(model.state_dict(), config.model_name)

    return scores


def plot(metrics, scores, epochs):
    x = np.asarray(range(1, epochs+1))
    i = 0
    for metric in metrics:
        try:
            y = np.asarray(scores[metric])
        except:
            print("Metric not found")

        plt.figure(i)
        plt.plot(x, y)
        plt.xlabel("epochs")
        plt.ylabel(metric)
        plt.savefig('../visualizations/'+metric+'-'+str(epochs)+'.png')
        i += 1


if __name__ == "__main__":

    torch.manual_seed(3)   # for reproducibility

    device = config.device
    epochs = config.epochs

    dataset_cls, train_loader, val_loader, test_loader, peptide_embedding, mhc_embedding = get_dataset(device)
    model = MHCAttnNet(peptide_embedding, mhc_embedding)
    # model.load_state_dict(torch.load(config.model_name))
    model.to(device)
    print(model)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters())

    scores = fit(model=model, train_dl=train_loader, val_dl=val_loader, loss_fn=loss_fn, opt=optimizer, epochs=epochs, device=device)

    metrics = ['loss', 'accuracy', 'precision', 'recall', 'roc_auc']
    plot(metrics, scores, epochs)
