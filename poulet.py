import comm

action = comm.make_action()
action.start()

try:
	while True:
		action.left_arm_half_deploy()
		action.right_arm_half_deploy()
		action.left_arm_deploy()
		action.right_arm_deploy()
finally:
	action.stop()