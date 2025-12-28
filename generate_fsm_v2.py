import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def setup_plot(title, subtitle=None, figsize=(6, 5)):
    plt.figure(figsize=figsize)
    plt.title(title, fontsize=12, fontweight='bold', pad=20)
    if subtitle:
        plt.text(0.5, 0.92, subtitle, ha='center', va='center', transform=plt.gcf().transFigure, fontsize=9, style='italic')
    plt.axis('off')

def draw_curved_edge(ax, u_pos, v_pos, rad=0.2, label=None, label_pos=0.5):
    arrow = mpatches.FancyArrowPatch(u_pos, v_pos,
                                   connectionstyle=f"arc3,rad={rad}",
                                   arrowstyle='-|>',
                                   mutation_scale=15,
                                   color='black')
    ax.add_patch(arrow)
    
    if label:
        mid_x = (u_pos[0] + v_pos[0]) / 2
        mid_y = (u_pos[1] + v_pos[1]) / 2
        if u_pos != v_pos:
            mid_y += rad * 0.5 
        plt.text(mid_x, mid_y, label, 
                 ha='center', va='center',
                 bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8),
                 fontsize=8)

def create_rotate_fsm():
    setup_plot("Robot Rotate Function FSM", "t_motion and t_stop can be modified in the code", figsize=(6, 4))
    
    G = nx.DiGraph()
    nodes = ['LEG_STOP', 'LEG_MOVING']
    G.add_nodes_from(nodes)
    
    pos = {
        'LEG_STOP': (-0.6, 0),
        'LEG_MOVING': (0.6, 0)
    }
    
    # Draw Nodes
    nx.draw_networkx_nodes(G, pos, node_size=4000, node_color='lightblue', edgecolors='black')
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold')
    
    # Annotations above nodes
    plt.text(pos['LEG_STOP'][0], pos['LEG_STOP'][1] + 0.25, "(for t_stop = 250ms)", ha='center', fontsize=9, color='darkblue')
    plt.text(pos['LEG_MOVING'][0], pos['LEG_MOVING'][1] + 0.25, "(for t_motion = 500ms)", ha='center', fontsize=9, color='darkblue')

    # Edges (Curved)
    ax = plt.gca()
    draw_curved_edge(ax, pos['LEG_STOP'], pos['LEG_MOVING'], rad=-0.3)
    draw_curved_edge(ax, pos['LEG_MOVING'], pos['LEG_STOP'], rad=-0.3)
    
    plt.tight_layout()
    plt.savefig("fsm_rotate.png", dpi=150)
    plt.close()
    print("Generated fsm_rotate.png")

def create_move_fsm():
    setup_plot("Robot Move Function FSM", figsize=(7, 6))
    
    G = nx.DiGraph()
    nodes = ['LEFT_STOP', 'RIGHT_MOVING', 'RIGHT_STOP', 'LEFT_MOVING']
    G.add_nodes_from(nodes)
    
    pos = {
        'LEFT_STOP': (0, 1),
        'RIGHT_MOVING': (1, 0),
        'RIGHT_STOP': (0, -1),
        'LEFT_MOVING': (-1, 0)
    }
    
    # Draw Nodes
    nx.draw_networkx_nodes(G, pos, node_size=3500, node_color='lightgreen', edgecolors='black')
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')

    ax = plt.gca()
    
    # Edges (Transitions)
    draw_curved_edge(ax, pos['LEFT_STOP'], pos['RIGHT_MOVING'], rad=-0.2)
    draw_curved_edge(ax, pos['RIGHT_MOVING'], pos['RIGHT_STOP'], rad=-0.2)
    draw_curved_edge(ax, pos['RIGHT_STOP'], pos['LEFT_MOVING'], rad=-0.2)
    draw_curved_edge(ax, pos['LEFT_MOVING'], pos['LEFT_STOP'], rad=-0.2)
    
    # Self Loops (Wait)
    def add_wait_label(node_name, time_str, offset_x, offset_y):
        p = pos[node_name]
        plt.text(p[0] + offset_x, p[1] + offset_y, f"Wait\nfor {time_str}", 
                 ha='center', va='center', fontsize=8, style='italic',
                 bbox=dict(boxstyle="round,pad=0.2", fc="lightyellow", ec="gray", alpha=0.9))

    add_wait_label('LEFT_STOP', '250ms', 0, 0.35)
    add_wait_label('RIGHT_MOVING', '500ms', 0.35, 0)
    add_wait_label('RIGHT_STOP', '250ms', 0, -0.35)
    add_wait_label('LEFT_MOVING', '500ms', -0.35, 0)

    plt.tight_layout()
    plt.savefig("fsm_move.png", dpi=150)
    plt.close()
    print("Generated fsm_move.png")

def create_arduino_loop_fsm():
    setup_plot("Arduino Main Loop Flow", figsize=(5, 6))
    
    G = nx.DiGraph()
    nodes = ['Start', 'Read Serial', 'Read Distance', 'Execute', 'Action']
    G.add_nodes_from(nodes)
    
    pos = {
        'Start': (0, 4),
        'Read Serial': (0, 3),
        'Read Distance': (0, 2),
        'Execute': (0, 1),
        'Action': (0, 0)
    }
    
    # Draw Nodes
    nx.draw_networkx_nodes(G, pos, node_size=2500, node_color='lightgray', edgecolors='black', node_shape='s')
    
    labels = {
        'Start': 'Start Loop',
        'Read Serial': 'Read Serial\n(Update Cmd)',
        'Read Distance': 'Read Distance\n(Check Obstacle)',
        'Execute': 'Select Action',
        'Action': 'Move/Rotate/Stop'
    }
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8)
    
    ax = plt.gca()
    
    # Straight down edges
    for i in range(4):
        u = list(pos.keys())[i]
        v = list(pos.keys())[i+1]
        ax.annotate("", xy=pos[v], xytext=pos[u], arrowprops=dict(arrowstyle="->", color="black"))
        
    # Loop back edge
    path_x = [0.2, 0.8, 0.8, 0.2]
    path_y = [0, 0, 4, 4]
    
    plt.plot(path_x, path_y, color='black', linestyle='--', linewidth=1)
    plt.text(0.85, 2, "Next Loop", rotation=270, va='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig("fsm_arduino_loop.png", dpi=150)
    plt.close()
    print("Generated fsm_arduino_loop.png")

if __name__ == "__main__":
    create_rotate_fsm()
    create_move_fsm()
    create_arduino_loop_fsm()
