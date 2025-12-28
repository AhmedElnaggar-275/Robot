import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def draw_fsm(G, pos, title, filename, node_colors=None):
    plt.figure(figsize=(10, 8))
    
    if node_colors is None:
        node_colors = ['lightblue'] * len(G.nodes())
        
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=5000, node_color=node_colors, edgecolors='black')
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold')
    
    # Draw edges with curvature
    ax = plt.gca()
    for u, v, data in G.edges(data=True):
        # Calculate control points for curved edges
        rad = 0.2
        if u == v:
            rad = 0.4 # Larger loop for self-loops
            
        # Check if bidirectional to adjust curvature
        if G.has_edge(v, u) and u != v:
            rad = 0.2
            
        label = data.get('label', '')
        
        # Draw edge
        arrow = mpatches.FancyArrowPatch(pos[u], pos[v],
                                       connectionstyle=f"arc3,rad={rad}",
                                       arrowstyle='-|>',
                                       mutation_scale=20,
                                       color='black')
        ax.add_patch(arrow)
        
        # Draw label (approximate position)
        # This is tricky in pure matplotlib/networkx without graphviz
        # We'll just put it near the midpoint
        mid_x = (pos[u][0] + pos[v][0]) / 2
        mid_y = (pos[u][1] + pos[v][1]) / 2
        
        # Offset for self loops
        if u == v:
            mid_y += 0.25
        
        plt.text(mid_x, mid_y, label, 
                 horizontalalignment='center', 
                 verticalalignment='center',
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.7),
                 fontsize=8)

    plt.title(title)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()
    print(f"Generated {filename}")

def create_move_fsm():
    G = nx.DiGraph()
    
    nodes = [
        'LEFT_STOP\n(Pause)', 
        'RIGHT_MOVING\n(Motion)', 
        'RIGHT_STOP\n(Pause)', 
        'LEFT_MOVING\n(Motion)'
    ]
    
    G.add_nodes_from(nodes)
    
    # Edges
    G.add_edge(nodes[0], nodes[0], label='< 250ms')
    G.add_edge(nodes[0], nodes[1], label='>= 250ms')
    
    G.add_edge(nodes[1], nodes[1], label='< 500ms')
    G.add_edge(nodes[1], nodes[2], label='>= 500ms')
    
    G.add_edge(nodes[2], nodes[2], label='< 250ms')
    G.add_edge(nodes[2], nodes[3], label='>= 250ms')
    
    G.add_edge(nodes[3], nodes[3], label='< 500ms')
    G.add_edge(nodes[3], nodes[0], label='>= 500ms')
    
    # Position in a circle
    pos = nx.circular_layout(G)
    
    draw_fsm(G, pos, "Robot Move Function FSM", "fsm_move.png")

def create_rotate_fsm():
    G = nx.DiGraph()
    
    nodes = [
        'LEG_STOP\n(Pause)', 
        'LEG_MOVING\n(Motion)'
    ]
    
    G.add_nodes_from(nodes)
    
    # Edges
    G.add_edge(nodes[0], nodes[0], label='< 250ms')
    G.add_edge(nodes[0], nodes[1], label='>= 250ms')
    
    G.add_edge(nodes[1], nodes[1], label='< 500ms')
    G.add_edge(nodes[1], nodes[0], label='>= 500ms')
    
    pos = nx.circular_layout(G)
    # Adjust positions to be left-right
    pos[nodes[0]] = [-1, 0]
    pos[nodes[1]] = [1, 0]
    
    draw_fsm(G, pos, "Robot Rotate Function FSM", "fsm_rotate.png")

def create_arduino_loop_fsm():
    G = nx.DiGraph()
    
    nodes = [
        'Start Loop',
        'Read Serial',
        'Read Distance',
        'Execute Cmd',
        'Move/Rotate/Stop'
    ]
    
    G.add_nodes_from(nodes)
    
    G.add_edge(nodes[0], nodes[1], label='')
    G.add_edge(nodes[1], nodes[2], label='Update Cmd')
    G.add_edge(nodes[2], nodes[3], label='Check Obstacle')
    G.add_edge(nodes[3], nodes[4], label='Action')
    G.add_edge(nodes[4], nodes[0], label='Next Loop')
    
    # Custom layout
    pos = {
        nodes[0]: [0, 1],
        nodes[1]: [0, 0.5],
        nodes[2]: [0, 0],
        nodes[3]: [0, -0.5],
        nodes[4]: [0, -1]
    }
    
    draw_fsm(G, pos, "Arduino Main Loop Flow", "fsm_arduino_loop.png")

if __name__ == "__main__":
    create_move_fsm()
    create_rotate_fsm()
    create_arduino_loop_fsm()
