import sys


class End:
    """
    Mutable wrapper for the global end index shared by all leaf edges.
    Incrementing end.value implicitly extends all open leaves in O(1) using trick 4, once a leaf, always a leaf.
    """
    def __init__(self):
        self.value = -1


class Node:
    """
    Represents a node in the suffix tree. Stores the edge as (start, end) indices into the text.
    """
    def __init__(self, start=None, end=None, node_id=None):
        self.node_id = node_id
        self.start = start  # trick 1: edge stored as (start, end) indices
        self.end = end
        self.children = {}
        self.link = None
        self.suffix_id = -1  # leaf suffix start (0-indexed), -1 for internal


class SuffixTree:
    """
    This class initialises the suffix tree with the input text
    appended with the terminal symbol $, creates the root node, and sets
    up the active point (skip-count pointer) and run log file.
    """
    def __init__(self, text, log_file="runlog.txt"):
        """
        Input:
            text (str): input string S[1...n] without terminal symbol
            log_file (str): path to the runlog output file

        Output:
            A SuffixTree instance ready to be built via build().
        """

        # append terminal symbol
        self.text = text + "$"
        self.global_end = End()  # trick 4: once a leaf, always a leaf

        # node id starts at 1
        self.next_node_id = 1
        self.root = self.create_node()
        self.root.link = self.root

        # skip count ptr
        self.active_node = self.root
        self.active_edge = -1
        self.active_length = 0

        self.remaining_suffix_count = 0
        self.prev_node = None  # last created internal node this phase
        self.log_file = open(log_file, "w")
        self.log_file.write(f"Root Node {self.root.node_id}\n\n")

    def create_node(self, start=None, end=None):
        """
        Function description: Creates and returns a new node with the next available node ID.

        Input:
            start (int): start index of the edge label in the text
            end (int or End): end index of the edge label

        Output:
            Node: newly created node
        """
        node = Node(start, end, self.next_node_id)
        self.next_node_id += 1
        return node

    def log(self, msg):
        self.log_file.write(msg + "\n")

    def log_active_state(self):
        """
        Function description: Logs the current active node ID, its suffix link target, and the remainder substring range in 1-based indexing to the runlog file.
        """
        # log active node and remainder in 1-indexed positions
        active_node_id = self.active_node.node_id
        link_id = self.active_node.link.node_id if self.active_node.link else active_node_id
        if self.active_length > 0:
            rem_start = self.active_edge + 1
            rem_end = self.active_edge + self.active_length
            rem_str = f"S[{rem_start}...{rem_end}]"
        else:
            rem_str = "EMPTY"
        self.log(
            f"    Active Node = Node {active_node_id} "
            f"(suffix link to Node {link_id}); "
            f"Remainder = {rem_str}"
        )

    def log_link(self, source, destination):
        """
        Function description: Logs the suffix link from source to destination.
        """
        self.log(f"        Linking Node {source} to Node {destination}")

    def end_value(self, node: Node):
        """
        Function description: Returns the integer end value of a node's edge, resolving the End object to its current value if the edge is a leaf edge.

        Input:
            node (Node): the node whose edge end value is needed

        Output:
            int: the end index of the node's incoming edge
        """
        return node.end.value if isinstance(node.end, End) else node.end

    def edge_length(self, node: Node):
        """
        Function description: Returns the number of characters on the incoming edge of a node. Returns 0 for the root since it has no incoming edge.

        Input:
            node (Node): the node whose edge length is needed

        Output:
            int: length of the incoming edge

        Time complexity:  O(1)
        Space complexity: O(1)
        """
        # root has no incoming edge
        if node is self.root:
            return 0
        return self.end_value(node) - node.start + 1

    def skip_count(self, node: Node):
        """
        Function description: Applies Trick 2 skip count: if active_length spans an entire edge, advance the skip count pointer past that edge in O(1) without comparing characters one by one.

        Input:
            node (Node): the child node at the end of the edge being considered

        Output:
            bool: True if the skip count pointer was advanced past this edge, False otherwise

        Time complexity:  O(1)
        Space complexity: O(1)
        """
        # trick 2: O(1) skip-count
        edge_len = self.edge_length(node)
        if self.active_length >= edge_len:
            self.active_edge += edge_len
            self.active_length -= edge_len
            self.active_node = node
            return True
        return False

    def extend(self, i: int):
        """
        Function description: Performs Ukkonen's algorithm by processing all explicit suffix extensions for character text[i], applying the three rules and four tricks taught in the lecture.

        Approach description:
            1. Utilizing Rule 1/Trick 4: increment global_end to implicitly extend all  open leaves in O(1).
            2. Increment remaining_suffix_count and compute the first explicit extension index.
            3. Loop over explicit extensions while remaining_suffix_count > 0:
               - No outgoing edge for the active character: Rule 2 alt - add new leaf directly off the active node, resolve any pending suffix link.
               - Outgoing edge exists: apply Trick 2 (skip-count) to advance the pointer if it spans the full edge.
               - Next character on edge matches text[i]: Rule 3 Trick 3 showstopper, resolve any pending suffix link.
               - Next character on edge differs: Rule 2 reg - split edge, create new internal node and leaf, resolve and set pending suffix link.
            4. After each Rule 2 extension, update the skip count pointer: shrink from root (root edge case) or follow suffix link.

        Input:
            i (int): position of the current character being processed

        Output:
            Updates the suffix tree in-place

        Time complexity: O(1) amortised per extension.
            Across all phases, Ukkonen performs O(n) total work.
            Therefore the total construction time is O(n).
        Space complexity: O(1) auxiliary per call
        """
        # rule 1 / trick 4: extend all open leaves implicitly via global_end
        self.global_end.value += 1

        # one more suffix needs to be explicitly inserted
        self.remaining_suffix_count += 1

        # j of first explicit extension this phase (0-indexed); display 1-indexed
        j_start = i - self.remaining_suffix_count + 1
        self.log(f"Phase {i + 1} starts from Extn {j_start + 1}")

        self.prev_node = None

        while self.remaining_suffix_count > 0:

            # current extension j (0-indexed suffix start)
            j = i - self.remaining_suffix_count + 1

            # pick active edge when at a node boundary
            if self.active_length == 0:
                self.active_edge = i

            edge_char = self.text[self.active_edge]

            if edge_char not in self.active_node.children:
                # rule 2 alt: no outgoing edge, hence add a new leaf directly
                self.log(f"    Extn {j + 1} applies Rule 2 (alternate)")
                self.log_active_state()

                leaf = self.create_node(i, self.global_end)
                leaf.suffix_id = j
                self.active_node.children[edge_char] = leaf
                self.log(f"        Node {leaf.node_id} created: Leaf node!")

                # resolve pending suffix link after creating the leaf
                if self.prev_node is not None:
                    self.log_link(self.prev_node.node_id, self.active_node.node_id)
                    self.prev_node.link = self.active_node
                    self.prev_node = None

                self.remaining_suffix_count -= 1

            else:
                child = self.active_node.children[edge_char]

                # trick 2: O(1) skip-count
                if self.skip_count(child):
                    continue

                pos = child.start + self.active_length

                if self.text[pos] == self.text[i]:
                    # rule 3: path already exists
                    self.log(f"    Extn {j + 1} applies Rule 3")
                    self.log_active_state()

                    # resolve pending suffix link
                    if self.prev_node is not None:
                        self.log_link(self.prev_node.node_id, self.active_node.node_id)
                        self.prev_node.link = self.active_node
                        self.prev_node = None

                    # trick 3: showstopper
                    self.active_length += 1
                    break

                else:
                    # rule 2 reg: split edge, insert new internal node and leaf
                    self.log(f"    Extn {j + 1} applies Rule 2 (regular)")
                    self.log_active_state()

                    old_start = child.start

                    # create internal node at the split point
                    new_node = self.create_node(
                        old_start, old_start + self.active_length - 1
                    )
                    new_node.link = self.root  # default suffix link to root
                    self.log(f"        Node {new_node.node_id} created: Internal node!")

                    # shorten old child edge to start after the split
                    child.start += self.active_length
                    new_node.children[self.text[child.start]] = child

                    # new leaf for the current suffix
                    leaf = self.create_node(i, self.global_end)
                    leaf.suffix_id = j
                    new_node.children[self.text[i]] = leaf
                    self.log(f"        Node {leaf.node_id} created: Leaf node!")

                    # redirect parent to the new internal node
                    self.active_node.children[self.text[old_start]] = new_node

                    # resolve pending suffix link after creating the new internal node
                    if self.prev_node is not None:
                        self.log_link(self.prev_node.node_id, new_node.node_id)
                        self.prev_node.link = new_node

                    self.prev_node = new_node
                    self.remaining_suffix_count -= 1

            # update skip count ptr for next extension
            if self.active_node is self.root and self.active_length > 0:
                # root edge case: shrink active length, shift active edge
                self.active_length -= 1
                self.active_edge = i - self.remaining_suffix_count + 1
            elif self.active_node is not self.root:
                # follow suffix link to skip to next active node in O(1)
                self.active_node = self.active_node.link

        # blank line to separate phases in output file
        self.log("")

    def build(self):
        """
        Function description: Runs all n+1 phases of Ukkonen's algorithm by calling extend(i) for each character index i in self.text.

        Output:
            Constructs the suffix tree in-place.

        Time complexity: O(n), where n = len(self.text)
        Space complexity: O(n) for the suffix tree nodes
        Space complexity analysis:
            The suffix tree contains O(n) nodes and edges.
            Each node stores constant-size attributes.
            Therefore total space is O(n).
        """
        for i in range(len(self.text)):
            self.extend(i)
        self.log_file.close()

    def compute_lcp(self):
        """
        Function description: Computes the LCP array by performing a single lexicographic DFS over the suffix tree, exploiting the tree structure directly.

        Approach description:
            1. Traverse children in sorted order at every internal node, this guarantees leaves are visited in lexicographical order.
            2. Pass first_leaf_lcp down through recursive calls:
               - The first child of any node inherits first_leaf_lcp unchanged from its caller.
               - Every subsequent child resets first_leaf_lcp to the current node's string depth, which equals the LCA depth between the last leaf of the previous subtree and the first leaf of this one.
            3. When a leaf is reached, append first_leaf_lcp to lcp. This gives LCP[k] = string depth of LCA(SA[k-1], SA[k]).

        Output:
            lcp (list[int]): LCP array of length N = n+1, where lcp[k] is the length of the longest common prefix between SA[k-1] and SA[k], with lcp[0] = 0 by convention.

        Time complexity: O(n), where n = len(self.text)
        Time complexity analysis:
            Each node is visited exactly once in the DFS. sorting over children at each node costs O(σ log σ) where σ <= 90 (constant alphabet size [37, 126]), so O(1) per node. edge_length() is O(1).
            Total: O(n).

        Space complexity: O(n)
        Space complexity analysis:
            The lcp array requires O(n) space. The recursion stack depth is O(n) in the worst case.
        """
        # lcp[k] = length of longest common prefix between SA[k-1] and SA[k]
        lcp = []

        def dfs(node: Node, node_depth: int, first_leaf_lcp: int):
            # node_depth: total characters from root to this node
            # first_leaf_lcp: LCP value to record when the first leaf of this subtree is reached
            if not node.children:  # leaf node
                lcp.append(first_leaf_lcp)  # record LCP
                return

            is_first_child = True
            for c in sorted(node.children.keys()):  # sort lexicographical order
                child = node.children[c]
                child_depth = node_depth + self.edge_length(child)
                if is_first_child:
                    dfs(child, child_depth, first_leaf_lcp)  # first child: LCP inherited unchanged from caller
                    is_first_child = False
                else:
                    dfs(child, child_depth, node_depth)  # later sibling: LCP = this node's depth

        # root depth = 0, first leaf LCP = 0
        dfs(self.root, 0, 0)
        return lcp


def main():
    if len(sys.argv) != 2:
        print("Usage: python suffix_tree.py <input_filename>")
        sys.exit(1)

    input_file = sys.argv[1]

    with open(input_file) as f:
        text = f.readline().rstrip("\n")

    suffix_tree = SuffixTree(text, log_file="runlog.txt")
    suffix_tree.build()

    lcp = suffix_tree.compute_lcp()

    with open("output.txt", "w") as out:
        for val in lcp:
            out.write(str(val) + "\n")


if __name__ == "__main__":
    main()
