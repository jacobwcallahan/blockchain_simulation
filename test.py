import simpy


def action_a(env):
    while True:
        print(f"Action A at time {env.now}")
        yield env.timeout(2)


def action_b(env):
    while True:
        print(f"Action B at time {env.now}")
        yield env.timeout(3)


env = simpy.Environment()
env.process(action_a(env))
env.process(action_b(env))
env.run(until=10)
