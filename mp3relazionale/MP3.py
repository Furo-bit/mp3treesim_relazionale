from lib2to3.pgen2.token import NOTEQUAL
import networkx as nx
import numpy as np
from collections import defaultdict, Counter
from pygraphviz import AGraph

class etichetta:
    
    def __init__(self, valore):
        self.valore=valore
        self.antenati=list()
        self.discendenti=list()
        self.conviventi=list()
        self.non_rel=list()

    
def read_dotfile(path, labeled_only=False, exclude=None): #Legge il file dell'albero
    T = nx.DiGraph(nx.drawing.nx_agraph.read_dot(path))
    return build_tree(T, labeled_only=labeled_only, exclude=exclude)

def build_tree(T, labeled_only=False, exclude=None): #costruisce l'albero
    if not nx.is_tree(T):
        raise ValueError("Not a valid tree.")

    label_to_nodes = defaultdict(set)
    label_set = set()
    node_to_labels = defaultdict(set)

    for node in T.nodes(data=True):
        id_node = node[0]

        if not 'label' in node[1] and not labeled_only:
            node[1]['label'] = str(node[0])
        if not 'label' in node[1] and labeled_only:
            node[1]['label'] = ''
            continue

        labels = node[1]['label'].split(',')
        for l in labels:
            if exclude:
                if l in exclude:
                    continue

            label_set.add(l)
            label_to_nodes[l].add(id_node)
            node_to_labels[id_node].add(l)

    label_set = sorted(list(label_set))

    return Tree(T, label_to_nodes, node_to_labels, label_set)

class Tree:
    def __init__(self, T, label_to_nodes, node_to_labels, label_set): #Classe albero
        self.T = T
        self.label_to_nodes = label_to_nodes
        self.node_to_labels = node_to_labels
        self.label_set = label_set
        self.label_list = self.build_etichette()

        self.LCA = LCA(self.T,
                       self.label_to_nodes,
                       self.node_to_labels)
    
    def build_etichette(self):
        x=list()
        for e in self.label_set:
            if e != "root":
                x.append(etichetta(e))
        return x
                
class LCA:
    def __init__(self, T, T_label_to_node, T_node_to_labels): #Classe LCA
        self.LCA_dict = dict()
        self.LCA_label_dict = T_label_to_node
        self.LCA_node2lbl = T_node_to_labels
        for lca in nx.tree_all_pairs_lowest_common_ancestor(T):
            self.LCA_dict[(lca[0][0], lca[0][1])] = lca[1]

    def lca_nodes(self, node1, node2):
        try:
            return self.LCA_dict[node1, node2]
        except:
            return self.LCA_dict[node2, node1]

    def lca_labels(self, label1, label2):
        nodes1 = self.LCA_label_dict[label1]
        nodes2 = self.LCA_label_dict[label2]

        lca_mset = Counter()
        for n1 in nodes1:
            for n2 in nodes2:
                lca_mset.update(self.lca_nodes(n1, n2))

        return lca_mset

    def label_to_node(self, label):
        return self.LCA_label_dict[label]

    def node_to_labels(self, node):
        return self.LCA_node2lbl[node]

    def __str__(self):
        return str(self.LCA_dict)

#Main
tree1 = read_dotfile('trees/treeEz1.gv')
tree2 = read_dotfile('trees/treeEz2.gv')

"""
for eti in tree1.label_list:
    print(eti.valore)

for x in tree1.T.successors('1'):
    print(x)

print(tree1.label_to_nodes['root'])
"""
for x in tree2.label_list:
    print("etichetta: " + x.valore + ", discendenti:")
    print(x.discendenti)

def ricorsione_discendente(tree, nodo):
    lista_discendenti=list()

    for figlio in tree.T.successors(nodo):
        lista_discendenti += ricorsione_discendente(tree, figlio)
        #print("lista dopo ricorsione: ")
        #print(lista_discendenti)
    for eti_in_nodo in tree.node_to_labels[nodo]:
        for eti_in_oggetto in tree.label_list:
            if (eti_in_nodo == eti_in_oggetto.valore):
                #print("lista prima dell'assegnazione: ")
                #print(lista_discendenti)
                eti_in_oggetto.discendenti=lista_discendenti
                #print(eti_in_oggetto.discendenti)

    for etichetta_in_nodo in tree.node_to_labels[nodo]:
        lista_discendenti += etichetta_in_nodo
    
    return lista_discendenti

iterator = iter(tree2.label_to_nodes['root'])
nodo_radice = next(iterator, None)
ricorsione_discendente(tree2, nodo_radice)

for x in tree2.label_list:
    print("etichetta: " + x.valore + ", discendenti:")
    print(x.discendenti)

 