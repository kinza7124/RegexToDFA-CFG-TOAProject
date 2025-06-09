from flask import Flask, render_template, request, jsonify
from automata.fa.nfa import NFA
from automata.fa.dfa import DFA
from graphviz import Digraph
from datetime import datetime
import matplotlib.pyplot as plt
import networkx as nx
import os
app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)))
# ----------------- Core Functions -----------------
def regex_to_dfa(regex_str):
    enfa = NFA.from_regex(regex_str)
    return DFA.from_nfa(enfa)

def generate_cfg(dfa):
    state_map = {state: f'Q{i}' for i, state in enumerate(dfa.states)}
    productions = {}
    for state in dfa.states:
        state_name = state_map[state]
        productions[state_name] = []
        for symbol, next_state in dfa.transitions[state].items():
            productions[state_name].append(f"{symbol} {state_map[next_state]}")
        if state in dfa.final_states:
            productions[state_name].append('ε')
    return {'start': state_map[dfa.initial_state], 'productions': productions}

def minimize_dfa(dfa):
    return dfa.minify()

def generate_pda(dfa):
    state_map = {state: f'q{i}' for i, state in enumerate(dfa.states)}
    transitions = []
    for state in dfa.states:
        for symbol, next_state in dfa.transitions[state].items():
            transitions.append({
                'current': state_map[state],
                'input': symbol,
                'pop': '⊥',
                'push': ['⊥'],
                'next': state_map[next_state]
            })
    return {
        'states': set(state_map.values()),
        'input_symbols': sorted(dfa.input_symbols),
        'stack_symbols': ['⊥'],
        'transitions': transitions,
        'initial_state': state_map[dfa.initial_state],
        'final_states': {state_map[state] for state in dfa.final_states},
        'initial_stack': '⊥'
    }
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        regex = request.form['regex']
        dfa = regex_to_dfa(regex)
        cfg = generate_cfg(dfa)
        pda = generate_pda(dfa)
        dfa_image = draw_automaton(dfa)  # Now returns base64 image
        return render_template('results.html', 
                             regex=regex,
                             dfa_image=dfa_image,
                             cfg=cfg,
                             pda=pda)
    return render_template('index.html')
# ----------------- Enhanced Features -----------------
def get_conversion_steps(regex):
    steps = [
        f"Input Regular Expression: {regex}",
        f"Processing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ]
    try:
        enfa = NFA.from_regex(regex)
        steps.append(f"Constructed ε-NFA with {len(enfa.states)} states")
        dfa = DFA.from_nfa(enfa)
        steps.append(f"Converted to DFA with {len(dfa.states)} states")
        steps.append("Successful Conversion")
    except Exception as e:
        steps.append(f"Conversion Error: {str(e)}")
    return steps

def analyze_complexity(dfa):
    return {
        'states': len(dfa.states),
        'transitions': sum(len(t) for t in dfa.transitions.values()),
        'time_complexity': f"O({len(dfa.states)})"
    }
# ----------------- Visualization -----------------
# def draw_automaton(dfa):
#     dot = Digraph()
#     dot.attr(rankdir='LR')
#     for state in dfa.states:
#         dot.node(str(state), shape='doublecircle' if state in dfa.final_states else 'circle')
#     dot.node('', shape='none', width='0', height='0')
#     dot.edge('', str(dfa.initial_state))
#     for src, transitions in dfa.transitions.items():
#         for symbol, dest in transitions.items():
#             dot.edge(str(src), str(dest), label=symbol)
#     return dot.pipe(format='svg').decode('utf-8')


def draw_automaton(dfa):
    G = nx.DiGraph()
    
    # Add states
    for state in dfa.states:
        G.add_node(state, final=(state in dfa.final_states))
    
    # Add transitions
    for src, transitions in dfa.transitions.items():
        for symbol, dest in transitions.items():
            G.add_edge(src, dest, label=symbol)
    
    # Draw graph
    pos = nx.spring_layout(G)
    plt.figure(figsize=(10, 8))
    
    # Draw nodes
    final_states = [n for n, attr in G.nodes(data=True) if attr['final']]
    non_final_states = [n for n in G.nodes if n not in final_states]
    
    nx.draw_networkx_nodes(G, pos, nodelist=non_final_states, node_size=1500, node_color='lightblue')
    nx.draw_networkx_nodes(G, pos, nodelist=final_states, node_size=1500, node_color='lightblue', node_shape='d')
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=20)
    
    # Draw labels
    nx.draw_networkx_labels(G, pos)
    edge_labels = {(u, v): d['label'] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    
    # Save to buffer
    from io import BytesIO
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode('utf-8')}"
if __name__ == '__main__':
    app.run(debug=True)
