import time

DICTIONARY = "datasets/dico_fr.txt"

ALPHABET = {"\x00": 0, "A":1,"B":2,"C":3,"D":4,"E":5,
            "F":6,"G":7,"H":8,"I":9,"J":10,
            "K":11,"L":12,"M":13,"N":14,"O":15,
            "P":16,"Q":17,"R":18,"S":19,"T":20,
            "U":21,"V":22,"W":23,"X":24,"Y":25,"Z":26}

# Alphabet but reversed
TEBAHPLA = {value:key for key, value in ALPHABET.items()}

# This class represents a node in the directed acyclic word graph (DAWG). It
# has a list of edges to other nodes. It has functions for testing whether it
# is equivalent to another node. Nodes are equivalent if they have identical
# edges, and each identical edge leads to identical states. The __hash__ and
# __eq__ functions allow it to be used as a key in a python dictionary.
class DawgNode:
    next_id = 0
    
    def __init__(self):
        self.id = DawgNode.next_id
        DawgNode.next_id += 1
        self.final = False
        self.edges = {}

        # Number of end nodes reachable from this one.
        self.count = 0

    def __str__(self):        
        arr = []
        if self.final: 
            arr.append("1")
        else:
            arr.append("0")

        for (label, node) in self.edges.items():
            arr.append( label )
            arr.append( str( node.id ) )

        return "_".join(arr)

    def __hash__(self):
        return self.__str__().__hash__()

    def __eq__(self, other):
        return self.__str__() == other.__str__()

    def num_reachable(self):
        # if a count is already assigned, return it
        if self.count: return self.count

        # count the number of final nodes that are reachable from this one.
        # including self
        count = 0
        if self.final: count += 1
        for node in self.edges.values():
            count += node.num_reachable()

        self.count = count
        return count

    def convert(self, label, readable=False):
        # NOTE: As there are specifically 42758 nodes in the DAWG of the French ODS 8,
        # every node id will hold in 16 bits
        if self.final:
            res = f"{0:016b}" + " "*readable
            res += "1"
        else:
            res = f"{list(self.edges.values())[0].id:016b}" + " "*readable
            res += "0"
        
        if self.count == 0:
            res += "1"
        else:
            res += "0"
        if readable:
            res += " " + label
        else:
            # As there are only 26 letters, 5 bits should be enough, but 6 bits
            # representation allow greater flexibility and still be at the 3 bytes total
            res += f"{ALPHABET[label]:06b}"
        return res


class Dawg:
    def __init__(self):
        self.previous_word = ""
        self.root = DawgNode()

        # Here is a list of nodes that have not been checked for duplication.
        self.unchecked_nodes = []

        # Here is a list of unique nodes that have been checked for
        # duplication.
        self.minimized_nodes = {}

        # Here is the data associated with all the nodes
        self.data = []

    def insert( self, word, data ):
        if word <= self.previous_word:
            raise ValueError("Error: Words must be inserted in alphabetical " +
                "order.")

        # find common prefix between word and previous word
        common_prefix = 0
        for i in range( min( len( word ), len( self.previous_word ) ) ):
            if word[i] != self.previous_word[i]: break
            common_prefix += 1

        # Check the unchecked_nodes for redundant nodes, proceeding from last
        # one down to the common prefix size. Then truncate the list at that
        # point.
        self._minimize( common_prefix )

        self.data.append(data)

        # add the suffix, starting from the correct node mid-way through the
        # graph
        if len(self.unchecked_nodes) == 0:
            node = self.root
        else:
            node = self.unchecked_nodes[-1][2]

        for letter in word[common_prefix:]:
            next_node = DawgNode()
            node.edges[letter] = next_node
            self.unchecked_nodes.append( (node, letter, next_node) )
            node = next_node

        node.final = True
        self.previous_word = word

    def finish( self ):
        # minimize all unchecked_nodes
        self._minimize( 0 )

        # go through entire structure and assign the counts to each node.
        self.root.num_reachable()

    def _minimize( self, down_to ):
        # proceed from the leaf up to a certain point
        for i in range( len(self.unchecked_nodes) - 1, down_to - 1, -1 ):
            (parent, letter, child) = self.unchecked_nodes[i]
            if child in self.minimized_nodes:
                # replace the child with the previously encountered one
                parent.edges[letter] = self.minimized_nodes[child]
            else:
                # add the state to the minimized nodes.
                self.minimized_nodes[child] = child
            self.unchecked_nodes.pop()

    def lookup( self, word ):
        node = self.root
        skipped = 0 # keep track of number of final nodes that we skipped
        for letter in word:
            if letter not in node.edges: return None
            for label, child in sorted(node.edges.items()):
                if label == letter: 
                    if node.final: skipped += 1
                    node = child
                    break
                skipped += child.count

        if node.final:
            return self.data[skipped]

    def node_count( self ):
        return len(self.minimized_nodes)

    def edge_count( self ):
        count = 0
        for node in self.minimized_nodes:
            count += len(node.edges)
        return count

    def display(self):
        stack = [self.root]
        done = set()
        while stack:
            node = stack.pop()
            if node.id in done: continue
            done.add(node.id)
            print("{}: ({})".format(node.id, node))
            for label, child in node.edges.items():
                print("\t{} goto {}".format(label, child.id))
                stack.append(child)

    def save_bin(self, filename):
        with open(filename, "wb") as file:
            stack = [("\x00", dawg.root)]
            done = set()
            while stack:
                label, node = stack.pop()
                if node in done:
                    continue
                done.add(node)
                node_bin = node.convert(label)
                node_bin = int(node_bin, 2)
                # all node representations are within 3 bytes, so we can set the byte_length to 3 bytes
                node_bin = node_bin.to_bytes(3, byteorder='big')
                file.write(node_bin)
                for child in node.edges.items():
                    stack.append(child)

    def save(self, filename):
        with open(filename, "w") as file:
            stack = [("\x00", dawg.root)]
            done = set()
            while stack:
                label, node = stack.pop()
                if node in done:
                    continue
                done.add(node)
                node_repr = node.convert(label, True)
                file.write(node_repr + "\n")
                for child in node.edges.items():
                    stack.append(child)


    # This method doesn't work very much
    # I need to actually work on how the data is stored normally
    @staticmethod
    def load_bin(filename):
        dawg = Dawg()
        with open(filename, "rb") as file:
            count = 0
            current = ""
            node = dawg.root
            for byte in file.read():
                count += 1
                current += f"{byte:08b}"
                
                if count%3 == 2:
                    child_id = int(current, 2)
                    current = ""
                elif count%3 == 0:
                    dawg._minimize(0)
                    next_node = DawgNode()
                    next_node.id = child_id
                    letter = TEBAHPLA[int(current[2:], 2)]
                    node.edges[letter] = next_node
                    next_node.final = current[0] == "1"
                    dawg.unchecked_nodes.append((node, letter, next_node))
                    node = next_node               
                    current = ""
        dawg.finish()
        return dawg


if __name__ == "__main__":
    dawg_file_bin = "DAWG/test_dico.bin"
    dawg_file_txt = "DAWG/test_dico.txt"

    WordCount = 3
    dawg = Dawg()
    dawg.finish()

    print("before saving")
    dawg.display()

    dawg.save_bin(dawg_file_bin)
    dawg = Dawg.load_bin(dawg_file_bin)
    
    print("\nafter saving")
    dawg.display()

    Edge_count = dawg.edge_count()
    print("Read {0} words into {1} nodes and {2} edges".format(
        WordCount, dawg.node_count(), Edge_count))
