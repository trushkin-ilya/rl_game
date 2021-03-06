from checkers import Checkers
from agent import Agent, MobileAgent
from utils import action_is_legal
import torch
from argparse import ArgumentParser
import os
from eval import get_score, eval


def generate_action_space():
    for x in range(32):
        increase_fwd_step = x // 4 % 2 == 0
        for forward_step in [3, 4]:
            yield (x, x + (forward_step + 1 if increase_fwd_step else forward_step))
        for backward_step in [3, 4]:
            yield (x, x - (backward_step if increase_fwd_step else backward_step + 1))
        for jump in [7, 9]:
            yield (x, x + jump)
            yield (x, x - jump)



if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--games', type=int, default=5000)
    parser.add_argument('--lr', type=int, default=3e-3)
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--gamma', type=float, default=0.99)
    parser.add_argument('--epsilon', type=float, default=1.0)
    parser.add_argument('--epsilon-decay', type=float, default=0.99978466)
    parser.add_argument('--checkpoints-dir', type=str,
                        default='../checkpoints')
    parser.add_argument('--save_every', type=int, default=100)
    parser.add_argument('--eval_every', type=int, default=1000)
    parser.add_argument('--save_dir', type=str, default='')
    args = parser.parse_args()

    action_space = torch.tensor(list(generate_action_space()))
    players = {'black':
               Agent(gamma=args.gamma,
                     epsilon=args.epsilon,
                     batch_size=args.batch_size,
                     action_space=action_space,
                     input_dims=[8*8+1],
                     lr=args.lr,
                     eps_dec=args.epsilon_decay),
               'white':
               Agent(gamma=args.gamma,
                     epsilon=args.epsilon,
                     batch_size=args.batch_size,
                     action_space=action_space,
                     input_dims=[8*8+1],
                     lr=args.lr,
                     eps_dec=args.epsilon_decay)}
    env = Checkers()
    initial_state = env.save_state()
    eps_history = []
    score = {'black': 0, 'white': 0}

    os.makedirs(args.checkpoints_dir, exist_ok=True)

    for i in range(args.games):
        print(f"episode={i}, score={score}, black_eps:{players['black'].epsilon}, white_eps:{players['white'].epsilon}")
        score = {'black': 0, 'white': 0}
        env.restore_state(initial_state)
        winner = None
        moves = torch.tensor(env.legal_moves())
        board, turn, last_moved_piece = env.save_state()
        brain = players[turn]
        board_tensor = torch.from_numpy(env.flat_board()).view(-1).float()
        encoded_turn = torch.tensor([1.]) if turn == 'black' else torch.tensor([0.])
        observation = torch.cat([board_tensor, encoded_turn])
        while not winner:
            action = brain.choose_action(observation)
            if not action_is_legal(action, moves):
                reward = -1000000
                new_turn = turn
            else:
                new_board, new_turn, _, moves, winner = env.move(*action.tolist())
                moves = torch.tensor(moves)
                turn_score, new_turn_score = (get_score(new_board, player) - get_score(board, player) for player in
                                              [turn, new_turn])
                reward = turn_score - new_turn_score
            score[turn] += reward
            board_tensor = torch.from_numpy(env.flat_board()).view(-1).float()
            encoded_turn = torch.tensor([1. if turn == 'black' else 0.])
            new_observation = torch.cat([board_tensor, encoded_turn])
            brain.store_transition(observation, action, reward, new_observation, bool(winner))
            brain.learn((observation != new_observation).any().item())
            observation = new_observation
            turn = new_turn
            brain = players[turn]

        if (i + 1) % args.save_every == 0:
            for key, agent in players.items():
                agent.net.eval()
                m_agent = MobileAgent(agent).cpu()
                path = os.path.join(args.checkpoints_dir, f'{key}[{i + 1}].pt')
                torch.jit.script(m_agent).save(path)
                agent.net.train()

        if i % args.eval_every == 0:
            for color, player in players.items():
                env.restore_state(initial_state)
                print(f'{color} score: {eval(player, env, color)}')