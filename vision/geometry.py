import numpy as np
import cv2

X, Y, Z = np.identity(3)


def cross_matrix(v):
    q = np.zeros((*v.shape[:-1], 3, 3), float)
    q[..., [2, 0, 1], [1, 2, 0]] = v
    q[..., [1, 2, 0], [2, 0, 1]] = -v
    # assert np.all(np.abs(x_mat(v, q)) < 1e-9)
    return q


def axle_rotation_matrices(axle, normalize=False):
    if normalize:
        axle = axle * dot(axle, axle)[..., None] ** -.5
    ellipses = '...' * (len(axle.shape) > 1)
    p = np.einsum('{0}i,{0}j->{0}ij'.format(ellipses), axle, axle)

    # I - P = -Q^2
    # assert np.all(np.abs(np.identity(3) - p + mat_mat(cross_matrix(axle), cross_matrix(axle))) < 1e-9)
    # P*P = P
    # assert np.all(np.abs(mat_mat(p, p) - p) < 1e-9)
    # P(axle) = axle
    # assert np.all(np.abs(mat_x(p, axle) - axle) < 1e-9)

    return p, np.identity(3) - p, cross_matrix(axle)


def axle_rotation(axle: np.ndarray, angle: float | np.ndarray, normalize=False):
    """
    Rotation matrix around axle

    :param axle:
    :param angle:
    :param normalize: True if you know |axle| != 1, it won't be checked
    :return:
    """
    if len(axle.shape) == 1 and isinstance(angle, np.ndarray) and angle.shape:
        _axle = axle
        axle = np.zeros((*angle.shape, 3), float)
        axle[..., :] = _axle
    # p: projection on vec(axle)
    # pt: projection on vec(axle).T
    # q: u => axle ^ u
    # c.f. https://fr.m.wikipedia.org/wiki/Matrice_de_rotation
    p, pt, q = axle_rotation_matrices(axle, normalize)

    # R_axle(angle) * axle = axle
    # assert np.all(np.abs(mat_x(p + np.cos(angle)[..., None, None] * pt + np.sin(angle)[..., None, None] * q, axle) - axle) < 1e-9)
    return p + np.cos(angle)[..., None, None] * pt + np.sin(angle)[..., None, None] * q


def render_multi_cam_cached_matrices(transformation_matrices, projection_matrices, points):
    """
    Render a set of points on both cameras
    :param transformation_matrices: shape (n, 4, 4), (camera_index, alpha_beta)
    :param projection_matrices: (n, 2, 4),
    :param points: shape (..., 3), (...point_index, xyz)
    :return: shape (n, ..., 2) (camera_index, ...point_index, xy)
    """
    # shape: (..., 4)
    v4_points = np.ones((*points.shape[:-1], 4))
    v4_points[..., :3] = points
    # shape (n, ..., 4)
    transformed = np.einsum('cik,...k->c...i', transformation_matrices, v4_points)
    # x division by y
    transformed[..., 0] /= transformed[..., 1]
    # z division by y
    transformed[..., 2] /= transformed[..., 1]

    return np.einsum('cik,c...k->c...i', projection_matrices, transformed)


MY_BASE_TO_CV2_BASE = np.array((
    (1., 0., 0.),
    (0., 0., -1.),
    (0., 1., 0.)
))

CV2_BASE_TO_MY_BASE = MY_BASE_TO_CV2_BASE.T


def mat_x(mat, x, out=None, extra='') -> np.ndarray:
    """
    Standard matrix/vector product, but with weird shapes
    """
    ellipses = '...' * (len(mat.shape) > 2), '...' * (len(x.shape) > 1)
    return np.einsum(f'{ellipses[0]}ik,{extra}{ellipses[1]}k->{extra}{max(ellipses)}i', mat, x, out=out)


def mat_mat(mat1, mat2, out=None):
    """
    Standard matrix/matrix product, but with weird shapes
    """
    ellipses = '...' * (len(mat1.shape) > 2), '...' * (len(mat2.shape) > 2)
    return np.einsum('{}ik,{}kj->{}ij'.format(*ellipses, max(ellipses)), mat1, mat2, out=out)


def dot(v1, v2, out=None):
    """
    Standard vector/vector dot product, but with weird shapes
    """
    ellipses = '...' * (len(v1.shape) > 1), '...' * (len(v2.shape) > 1)
    return np.einsum(f'{ellipses[0]}k,{ellipses[1]}k->{max(ellipses)}', v1, v2, out=out)


def sign(_x, zero=0.):
    return 2 * (_x > zero) - 1


def find_orientation(rotation_matrix):
    """
    Recovers yaw(alpha), pitch(beta), roll(gamma) from rotation_matrix
    """
    yp = mat_x(rotation_matrix, Y)
    x, y, z = dot(X, yp), dot(Y, yp), dot(Z, yp)
    xy_mag = (x * x + y * y) ** .5
    alpha: np.ndarray = np.arccos(y / xy_mag) * sign(-x)
    beta: np.ndarray = np.arccos(xy_mag) * sign(z)

    r_gamma = mat_mat(axle_rotation(X, -beta), mat_mat(axle_rotation(Z, -alpha), rotation_matrix))
    zp = mat_x(r_gamma, Z)
    gamma: np.ndarray = np.arccos(np.minimum(1, np.maximum(-1, dot(Z, zp)))) * sign(dot(X, zp))
    return np.concatenate((alpha[..., None], beta[..., None], gamma[..., None]), axis=-1)


def screen_to_ray(ray_matrix, points, projection_matrix=None) -> np.ndarray:
    """
    Point on a screen, becomes a ray cast from the camera (projection matrix was used to test, you can put None)

    :param ray_matrix: np.ndarray, shape (3, 3)
    :param points: np.ndarray, shape (..., 2)
    :param projection_matrix, used to debug
    """
    rays = np.ones((*points.shape[:-1], 3), float)
    rays[..., ::2] = points
    mat_x(ray_matrix, rays, out=rays)
    rays *= dot(rays, rays)[..., None] ** -.5

    # tester = np.ones((*rays.shape[:-1], 4), float)
    # tester[..., :3] = rays / rays[..., 1, None]
    # assert np.all(np.abs(mat_x(projection_matrix, tester) - points) < 1e-9)
    return rays


def opencv_save_my_ass(obj_points: np.ndarray, img_points: np.ndarray, camera_matrix: np.ndarray) -> np.ndarray:
    """
    Solves the camera position given real points and their corresponding img points, much better than
    `find_camera_position`, no hard feelings

    :param obj_points: np.ndarray, shape (n, 3), (point_index, xyz)
    :param img_points: np.ndarray, shape (n, 2), (point_index, xy)
    :param camera_matrix: np.ndarray, shape (3, 3)
    | f_x  0   vx |
    |  0  f_y  vy |
    |  0   0   1  |
    :return: camera screw: np.ndarray, shape (3, 2)
    |  x  alpha(yaw)   |
    |  y  beta(pitch)  |
    |  z  gamma(roll)  |
    """

    # Opencv uses a weird base, conversion is necessary
    _, r_vec, t_vec = cv2.solvePnP(mat_x(MY_BASE_TO_CV2_BASE, obj_points), img_points, camera_matrix, np.array(()))
    # Euler said rotation matrices can be described with only one vector, hence `r_vec.shape = (3,)`
    r = cv2.Rodrigues(-r_vec)[0]
    result_screw = np.zeros((3, 2), float)
    result_screw[:, 0] = CV2_BASE_TO_MY_BASE @ r @ -t_vec[:, 0]
    result_screw[:, 1] = find_orientation(CV2_BASE_TO_MY_BASE @ r @ MY_BASE_TO_CV2_BASE)
    return result_screw


"""
Past this point is a desperate attempt to match the above function. Developed before the discovery of the holy function
`cv2.solvePnP`, `find_camera_position` works  fine, but is outperformed due to its poor sensitivity to noise, it still 
requires finishing to chose reliably good construction points (c.f. GUI tests: test_real.py, 
really_ideal_situations.py). However, the maths involved were pleasing, so it deserves to survive. Plus, some survivors 
(quite a lot actually) had to be dragged above this checkpoint to complete the rest of the code and it may happen again.

In this uncharted territory, you may find scarce amounts of comments or documentation and old asserted statements that 
are disengaged for your safety and that certainly do not correlate any patience drop. 

At your own risks,
kisses,
Loïc
"""


def det(v1, v2):
    return v1[..., 0] * v2[..., 1] - v1[..., 1] * v2[..., 0]


def x_mat(x, mat, out=None):
    ellipses = '...' * (len(x.shape) > 1), '...' * (len(mat.shape) > 2)
    return np.einsum(f'{ellipses[0]}k,{ellipses[1]}kj->{max(ellipses)}j', x, mat, out=out)


def cross(v1, v2):
    return mat_x(cross_matrix(v1), v2)


def mixt(v0, v1, v2):
    ellipses = '...' * (len(v0.shape) > 1), '...' * (len(v1.shape) > 1), '...' * (len(v2.shape) > 1)
    return np.einsum('{}i,{}ij,{}j->{}'.format(*ellipses, max(ellipses)), v0, cross_matrix(v1), v2)


def sc_intersection(sc_points):
    v0, v1, v2 = sc_points[2] - sc_points[0], sc_points[1] - sc_points[0], sc_points[3] - sc_points[2]
    k1 = (det(v2, v0) / det(v2, v1))[..., None]
    # is computed point on the second line
    # assert np.all(np.abs(det(sc_points[0] + v1 * k1 - sc_points[2], v2)) < 1e-9)
    return sc_points[0] + v1 * k1


def re_intersection(re_points):
    v0, v1, v2 = re_points[2] - re_points[0], re_points[1] - re_points[0], re_points[3] - re_points[2]
    k1 = mixt(Z, v2, v0) / mixt(Z, v2, v1)
    # is computed point on the second line
    # assert np.all(np.abs(mixt(Z, re_points[0] + v1 * k1 - re_points[2], v2)) < 1e-9)
    return re_points[0] + v1 * k1


def rotate_to_z0(rays):
    angle = np.arccos(dot(Y, rays[0]))
    axle = cross(Y, rays[0])
    r0 = axle_rotation(axle, -angle, True)
    mat_x(r0, rays, out=rays, extra='n')

    x, z = dot(X, rays[1]), dot(Z, rays[1])
    angle = np.arccos(x * (x ** 2 + z ** 2) ** -.5) * sign(z)
    r1 = axle_rotation(Y, angle)
    mat_x(r1, rays, out=rays, extra='n')

    # Z = 0
    # assert np.all(np.abs(dot(Z, rays)) < 1e-9)
    # ||rays|| = 1
    # assert np.all(np.abs(dot(rays, rays) - 1) < 1e-9)
    return mat_mat(r1, r0)


def solve_3pr(re_points, sc_points, re_point5, sc_point5, ray_matrix, index, projection_matrix):
    sl = (slice(None, 2), slice(2, None))[index]
    p1, p2, p3 = re_diag = np.concatenate((re_points[sl], re_point5[None]), axis=0)
    sc_diag = np.concatenate((sc_points[sl], sc_point5[None]), axis=0)

    u1, u2, u3 = rays = screen_to_ray(ray_matrix, sc_diag, projection_matrix)
    r10 = rotate_to_z0(rays)

    c1, c3 = mixt(Z, u1, u2), mixt(Z, u3, u2)
    v12, v23 = p2 - p1, p3 - p2
    x, y = mixt(Z, u3, v23) * c1 + mixt(Z, u1, v12) * c3, dot(u3, v23) * c1 + dot(u1, v12) * c3

    angle = np.pi * .5 + np.arccos(x * (x**2 + y**2) ** -.5) * sign(y)
    r2 = axle_rotation(Z, -angle)
    mat_x(r2, rays, out=rays, extra='n')

    inter = p1 + u1 * mixt(Z, u2, v12) / mixt(Z, u2, u1)
    behind_cam = dot(u1, p1 - inter) < 0
    r2[behind_cam, :2, :2] = -r2[behind_cam, :2, :2]
    rays[:, behind_cam, :] = -rays[:, behind_cam, :]

    # assert np.all(np.abs(dot(re_diag - inter, rays) - dot(re_diag - inter, re_diag - inter) ** .5) < 1e-9)
    # ray linearity
    # assert np.all(np.abs(cross(re_diag - inter, rays)) < 1e-9)
    # in front of cam
    # assert np.all(dot(rays, re_diag - inter) >= 0)

    return re_diag, mat_mat(r2, r10), inter, rays


def paste_3pr(rays0, rays1, inter0, re_diag0, re_diag1):
    axle0, axle1 = re_diag0[1] - re_diag0[0], re_diag1[1] - re_diag1[0]
    p0, pt0, q0 = axle_rotation_matrices(axle0, True)
    v0, v1 = rays0[2], rays1[2]

    k0 = dot(axle1, v1 - mat_x(p0, v0))
    x, y = dot(mat_x(pt0, v0), axle1), dot(mat_x(q0, v0), axle1)
    inv_mag = (x ** 2 + y ** 2) ** -.5

    angle0 = np.arccos(np.maximum(-1., np.minimum(1., x * inv_mag))) * sign(y)  # sign(x) * np.pi
    acos_k0 = np.arccos(k0 * inv_mag)
    angle = angle0 + acos_k0
    r3 = p0 + np.cos(angle)[..., None, None] * pt0 + np.sin(angle)[..., None, None] * q0
    cam_pos = re_diag0[0] + mat_x(r3, inter0 - re_diag0[0])
    under_table = dot(cam_pos, Z) < 0
    cam_pos[under_table, 2] *= -1
    r3[under_table, :, :] = p0 + np.cos(angle - 2 * acos_k0)[..., None, None] * pt0 + np.sin(angle - 2 * acos_k0)[..., None, None] * q0

    # assert np.all(dot(cam_pos, Z) >= 0)
    # assert np.all(np.abs(dot(mat_x(r3, rays0[2]), axle1 * dot(axle1, axle1) ** -.5 - axle0 * dot(axle0, axle0) ** -.5)) < 1e9)
    return r3, cam_pos


def find_camera_position(re_points, sc_points, ray_matrix, projection_matrix=None):
    """
    Forget about it and go use `opencv_save_my_ass`, no hard feelings
    """
    re_point5 = re_intersection(re_points)
    sc_point5 = sc_intersection(sc_points)

    re_diag0, r210_0, inter0, rays0 = solve_3pr(re_points, sc_points, re_point5, sc_point5, ray_matrix, 0, projection_matrix)
    re_diag1, r210_1, inter1, rays1 = solve_3pr(re_points, sc_points, re_point5, sc_point5, ray_matrix, 1, projection_matrix)
    # assert np.all(np.abs(dot(rays0[2], re_point5 - inter0) - dot(rays1[2], re_point5 - inter1)) < 1e-9)

    r3_0, cam0 = paste_3pr(rays0, rays1, inter0, re_diag0, re_diag1)
    r3_1, cam1 = paste_3pr(rays1, rays0, inter1, re_diag1, re_diag0)

    mat_x(r3_0, rays0, out=rays0, extra='n')
    mat_x(r3_1, rays1, out=rays1, extra='n')

    # assert np.all(np.abs(dot(rays0[2], re_point5 - cam0) - dot(rays1[2], re_point5 - cam1)) < 1e-9)
    # assert np.all(np.abs(cam1 - cam0) < 1e-4)

    r_tot0, r_tot1 = mat_mat(r3_0, r210_0), mat_mat(r3_1, r210_1)
    # assert np.all(np.abs(r_tot0 - r_tot1) < 1e-6)
    ori0 = find_orientation(r_tot0)
    ori1 = find_orientation(r_tot1)

    # assert np.all(np.abs(ori0 - ori1) < 1e-6)
    return cam0, ori0, cam1, ori1
