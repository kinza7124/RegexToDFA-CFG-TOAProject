from flask import Flask, render_template, request, jsonify
from automata.fa.nfa import NFA
from automata.fa.dfa import DFA
from graphviz import Digraph
from datetime import datetime
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
        dfa_svg = draw_automaton(dfa)
        return render_template('results.html', 
                             regex=regex,
                             dfa_svg=dfa_svg,
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
def draw_automaton(dfa):
    dot = Digraph()
    dot.attr(rankdir='LR')
    for state in dfa.states:
        dot.node(str(state), shape='doublecircle' if state in dfa.final_states else 'circle')
    dot.node('', shape='none', width='0', height='0')
    dot.edge('', str(dfa.initial_state))
    for src, transitions in dfa.transitions.items():
        for symbol, dest in transitions.items():
            dot.edge(str(src), str(dest), label=symbol)
    return dot.pipe(format='svg').decode('utf-8')

if __name__ == '__main__':
    app.run(debug=True)
