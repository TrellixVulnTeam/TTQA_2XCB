
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from collections import OrderedDict
import dgl


#定义Mydataset继承自Dataset,并重写__getitem__和__len__
class TTQADGLdataset(Dataset):
    def __init__(self, all_input_ids, all_input_mask, all_segment_ids, all_label_ids,
                       all_graph1_nodeid_to_inputids, all_graph1_dgl,
                       all_graph2_nodeid_to_inputids, all_graph2_dgl, all_graph3_dgl):
        super(TTQADGLdataset, self).__init__()
        self.num = len(all_input_ids) #生成多少个点（多少个数据）
        self.all_input_idx = all_input_ids
        self.all_input_mask = all_input_mask
        self.all_segment_ids = all_segment_ids
        self.all_label_ids = all_label_ids
        self.all_graph1_nodeid_to_inputids = all_graph1_nodeid_to_inputids
        self.all_graph1_dgl = all_graph1_dgl
        self.all_graph2_nodeid_to_inputids = all_graph2_nodeid_to_inputids
        self.all_graph2_dgl = all_graph2_dgl
        self.all_graph3_dgl = all_graph3_dgl

    # indexing
    def __getitem__(self, index):
        input_idx = self.all_input_idx[index]
        input_mask = self.all_input_mask[index]
        segment_ids = self.all_segment_ids[index]
        label_ids = self.all_label_ids[index]
        graph1_nodeid_to_inputids = self.all_graph1_nodeid_to_inputids[index]
        graph1_dgl = self.all_graph1_dgl[index]
        graph2_nodeid_to_inputids = self.all_graph2_nodeid_to_inputids[index]
        graph2_dgl = self.all_graph2_dgl[index]
        graph3_dgl = self.all_graph3_dgl[index]
        return input_idx, input_mask, segment_ids, label_ids, graph1_nodeid_to_inputids, graph1_dgl, graph2_nodeid_to_inputids, graph2_dgl, graph3_dgl

    def __len__(self):
        return self.num


class TTQADGLDataLoader(DataLoader):
    def __init__(self, dataset, device, eval=False, **kwargs):
        if kwargs.get('collate_fn', None) is None:
            kwargs['collate_fn'] = self._collate_fn
        self.eval = eval
        self.device = device
        super().__init__(dataset, **kwargs)

    def _collate_fn(self, batch_data):
        """
            input_ids, input_mask, segment_ids, label_ids,\
            graph1_nodeid_to_inputids, all_blag_to_uri_dict, all_graph1_nx,\
            graph2_nodeid_to_inputids, all_graph2_nx = batch
        :param batch_data:
        :return:
        """
        batch = list(zip(*batch_data))
        assert len(batch) == 9
        tensorized = OrderedDict()
        tensorized['input_ids'] = torch.LongTensor(batch[0]).to(self.device)
        tensorized['input_mask'] = torch.LongTensor(batch[1]).to(self.device)
        tensorized['segment_ids'] = torch.LongTensor(batch[2]).to(self.device)
        tensorized['label_ids'] = torch.LongTensor(batch[3]).to(self.device)
        tensorized['graph1_nodeid_to_inputids'] = batch[4]
        tensorized['graph2_nodeid_to_inputids'] = batch[6]
        """dgl batch_graphs"""
        g1g2_dgl_graphs_list = []
        graph_idx = []
        g3_dgl_graphs_list = []
        index = 0
        for graph1, graph2, graph3 in zip(batch[5], batch[7], batch[8]):
            g1g2_dgl_graphs_list.append(graph1)
            g1g2_dgl_graphs_list.append(graph2)
            graph_idx.append(np.ones(graph1.number_of_nodes(), dtype=np.int32) * index)
            index += 1
            graph_idx.append(np.ones(graph2.number_of_nodes(), dtype=np.int32) * index)
            index += 1
            g3_dgl_graphs_list.append(graph3)
        tensorized['g1g2_batch_graphs'] = dgl.batch(g1g2_dgl_graphs_list).to(self.device)
        tensorized['graph_idx'] = torch.from_numpy(np.concatenate(graph_idx, axis=0)).long().to(self.device)
        tensorized['g3_batch_graphs'] = dgl.batch(g3_dgl_graphs_list).to(self.device)
        return tensorized

