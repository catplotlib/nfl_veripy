from .Dynamics import ContinuousTimeDynamics
import numpy as np
import cvxpy as cp
from scipy.linalg import solve_discrete_are
import osqp


class Quadrotor(ContinuousTimeDynamics):
    def __init__(self):

        g = 9.8  # m/s^2

        At = np.zeros((6, 6))
        At[0][3] = 1
        At[1][4] = 1
        At[2][5] = 1

        bt = np.zeros((6, 3))
        # bt[3][0] = g
        # bt[4][1] = -g
        # bt[5][2] = 1
        bt[3][0] = 1
        bt[4][1] = -1
        bt[5][2] = 1

        ct = np.zeros((6,))
        ct[-1] = -g
        # import pdb; pdb.set_trace()

        # u_limits = None
        # u_limits = np.array(
        #     [
        #         [-np.pi / 3, np.pi / 3],
        #         [-np.pi / 3, np.pi / 3],
        #         [0, 2 * g],
        #     ]
        # )

        # # x_limits = 2*np.array(
        # #     [
        # #         [-100, 100],
        # #         [-100, 100],
        # #         [-100, 100],
        # #         [-0.5, 0.5],
        # #         [-0.5, 0.5],
        # #         [-0.05, 0.05],
        # #     ]
        # # )
        # # 
        # x_limits = {3: [-2,2], 4: [-2,2], 5: [-2,2]}


        u_limits = 1*np.array(
            [
                [-8, 8],
                [-8, 8],
                [1.8, 17.8]
            ]
        )

        x_limits = {3: [-0.5,0.5], 4: [-0.5,0.5], 5: [-0.5,0.5]}

        dt = 0.125

        super().__init__(At=At, bt=bt, ct=ct, u_limits=u_limits, dt=dt, x_limits=x_limits)
        Q_ = np.zeros((6,6))
        Q_[0,0], Q_[1,1], Q_[2,2] = 2, 2, 1
        self.Q = Q_
        self.R = 0.2*np.eye(3)
        self.safe_dist = 0.3
        

        self.cmap_name = "tab20"

    
    def control_mpc(self, x0):
        # LQR-MPC parameters
        if not hasattr(self, "Q"):
            self.Q = np.eye(6)
        if not hasattr(self, "R"):
            self.R = 1
        if not hasattr(self, "Pinf"):
            self.Pinf = solve_discrete_are(self.At, self.bt, self.Q, self.R)
        if not hasattr(self, "safe_dist"):
            self.safe_dist = 0.3

        obstacle_coords = np.array(
            [
                [-1,0]
            ]
        )

        return self.control_quadrotor_mpc(
            x0,
            self.At,
            self.bt,
            self.ct,
            self.Q,
            self.R,
            self.Pinf,
            self.u_limits[:, 0],
            self.u_limits[:, 1],
            obstacle_coords,
            self.safe_dist,
            n_mpc=20,
            debug=False,
        )

    
    def control_quadrotor_mpc(self, x0s, A, b, c, Q, R, P, u_min, u_max, obstacle_coords, safe_dist, n_mpc=10, debug=False):
        # TODO: account for final state constraint using O_inf

        x0s[0] = np.array([-2,0.3,0.0,0,0,0])

        us = np.empty((x0s.shape[0], b.shape[1]))
        for i, x0 in enumerate(x0s):
            # print(x0)
            u = cp.Variable((n_mpc, b.shape[1]))
            x = cp.Variable((n_mpc + 1, x0.shape[0]))

            cost = 0

            constrs = []
            constrs.append(x[0, :] == x0)
            step = 0
            while step < n_mpc:

                # import pdb; pdb.set_trace()
                constr = x[step + 1, :] == self.dynamics_step(x[step, :],u[step, :])
                constrs.append(constr)

                # Input constraints
                constrs.append(u[step] <= u_max)
                constrs.append(u[step] >= -u_max)

                # State constraints
                for obstacle in obstacle_coords:
                    # import pdb; pdb.set_trace()
                    dist = cp.norm(x[step + 1, 0:2]-obstacle, np.inf)
                    cost += cp.inv_prod(x[step + 1, 0:2])

                constrs.append(x[step + 1, 3:] >= -0.5)
                constrs.append(x[step + 1, 3:] <= 0.5)

                # Control cost
                cost += cp.quad_form(u[step], R)

                # State stage cost
                cost += cp.quad_form(x[step, :], Q)

                step += 1

            # Terminal state constraint
            # constrs.append()

            # Terminal state cost
            cost += cp.quad_form(x[n_mpc, :], P)
            

            prob = cp.Problem(cp.Minimize(cost), constrs)

            prob.solve()

            if debug:
                print(x.value)

            import pdb; pdb.set_trace()

            us[i] = u.value[0, :]
        return us