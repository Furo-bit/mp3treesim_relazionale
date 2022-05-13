from os import remove
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

def build_tree(T, labeled_only=False, exclude=None): #Costruisce l'albero
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

#Metodi per relazioni
def build_relazioni_ricorsione(tree, nodo):
    lista_discendenti=list()
    
    for figlio in tree.T.successors(nodo):
        lista_aggiornamento = build_relazioni_ricorsione(tree, figlio)
        lista_discendenti += lista_aggiornamento
        #Non Relazionati
        for figlio2 in tree.T.successors(nodo):
            if figlio != figlio2:
                build_non_relazionate(tree, figlio2, lista_aggiornamento)

    for eti_in_nodo in tree.node_to_labels[nodo]:
        if eti_in_nodo != "root":
            for eti_in_oggetto in tree.label_list:
                if (eti_in_nodo == eti_in_oggetto.valore):
                    #Discendenti
                    eti_in_oggetto.discendenti += lista_discendenti
                    #Conviventi
                    lista_conviventi=list(tree.node_to_labels[nodo])
                    lista_conviventi.remove(eti_in_oggetto.valore)
                    eti_in_oggetto.conviventi += lista_conviventi
                for elemento in lista_discendenti:
                    if (eti_in_oggetto.valore == elemento):
                        #Antenati
                        eti_in_oggetto.antenati += eti_in_nodo
            

    for etichetta_in_nodo in tree.node_to_labels[nodo]:
        lista_discendenti += etichetta_in_nodo
    
    return lista_discendenti
    
def build_non_relazionate(tree, nodo, lista): #Aggiunta di etichette non relazionate
    for eti_in_nodo in tree.node_to_labels[nodo]:
        for eti_in_oggetto in tree.label_list:
            if (eti_in_nodo == eti_in_oggetto.valore):
                eti_in_oggetto.non_rel += lista
    
    for figlio in tree.T.successors(nodo):
        build_non_relazionate(tree, figlio, lista)

def build_relazioni(tree): #Metodo per la chiamata ai metodi che aggiungono relazioni
    iterator = iter(tree.label_to_nodes['root'])
    nodo_radice = next(iterator, None)
    build_relazioni_ricorsione(tree, nodo_radice)

def visualizza_relazioni(tree): #Visualizzazione delle relazioni
    for x in tree.label_list: 
        print("Relazioni di " + x.valore)
        print("Antenati: ")
        print(x.antenati)
        print("Discendenti: ")
        print(x.discendenti)
        print("Conviventi: ")
        print(x.conviventi)        
        print("Non relazionati: ")
        print(x.non_rel)
        print("-------------------------------")

def mp3_relazioni(tree):
    build_relazioni(tree)
    visualizza_relazioni(tree)

#Metodi per MTT
def MTT_date_3_etichette(a, b, c): #Comprensione della configurazione MTT
    configurazione = 0;
    if len(a.discendenti) == 2 or len(b.discendenti) == 2 or len(c.discendenti) == 2 : #tutte
        #1,5,7
        if len(a.conviventi == 1) or len(b.conviventi == 1) or len(c.conviventi == 1):
            #7
            configurazione = 7
        elif len(a.non_rel == 1) or len(b.non_rel == 1) or len(c.non_rel == 1):
            #5
            configurazione = 5
        else:
            #1
            configurazione = 1    
    elif len(a.non_rel) == 0 or len(b.non_rel) == 0 or len(c.non_rel) == 0: #2,3,4,6,8,9
        if len(a.non_rel) == 0 and len(b.non_rel) == 0 and len(c.non_rel) == 0: #2,3,4,8
            #2,4
            #uso di LCA
            configurazione = 24
        elif len(a.conviventi > 0) or len(b.conviventi > 0) or len(c.conviventi > 0): #3,8
            #8
            configurazione = 8
        else:
            #3   
            configurazione = 3  
    elif len(a.conviventi) == 2 and len(b.conviventi) == 2 and len(c.conviventi) == 2: #6,9
        #9
        configurazione = 9
    else:
        #6
        configurazione = 6
    return configurazione    

def filtro_etichetta(etichetta, valore1, valore2, valore3):
    for elemento in etichetta.antenati:
        if elemento != valore1 or elemento != valore2 or elemento != valore3:
            etichetta.antenati.remove(elemento)
    for elemento in etichetta.discendenti:
        if elemento != valore1 or elemento != valore2 or elemento != valore3:
            etichetta.discendenti.remove(elemento)
    for elemento in etichetta.conviventi:
        if elemento != valore1 or elemento != valore2 or elemento != valore3:
            etichetta.conviventi.remove(elemento)
    for elemento in etichetta.non_rel:
        if elemento != valore1 or elemento != valore2 or elemento != valore3:
            etichetta.non_rel.remove(elemento)
    return etichetta



#Main
tree = read_dotfile('trees/treeEz1.gv')
mp3_relazioni(tree)


 