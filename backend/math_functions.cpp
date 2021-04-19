#include <cmath>
#include <vector>
#include <array>

#include "logging_functions.h"

using std::sin, std::cos, std::sqrt, std::pow, std::abs;

typedef std::vector<std::vector<int>> int2dvec_t;
typedef std::vector<std::vector<double>> double2dvec_t;

// Function to return matrix vector product of basis A(2,2) with vector(2)
template <typename T1, typename T2>
std::vector<T1> basis_2x2_dot_2d_vector(const std::vector<std::vector<T1>> &basis, std::vector<T2> &vec)
{
    std::vector<T1> result;
    for (int i = 0; i < 2; i++)
    {
        result.push_back(basis[i][0] * vec[0] + basis[i][1] * vec[1]);
    }
    return result;
};

template std::vector<int> basis_2x2_dot_2d_vector<int, int>(const std::vector<std::vector<int>> &basis, std::vector<int> &vec);
template std::vector<double> basis_2x2_dot_2d_vector<double, int>(const std::vector<std::vector<double>> &basis, std::vector<int> &vec);
template std::vector<double> basis_2x2_dot_2d_vector<double, double>(const std::vector<std::vector<double>> &basis, std::vector<double> &vec);

// Function to rotate vector(2) by angle theta in degrees
template <typename T>
std::vector<double> rotate_2d_vector(std::vector<T> &vec, const double &theta)
{
    std::vector<double> result = {0.0, 0.0};
    double t = theta * 2 * M_PI / 180.0;
    double R[2][2] = {{cos(t), -sin(t)}, {sin(t), cos(t)}};
    result[0] = R[0][0] * vec[0] + R[0][1] * vec[1];
    result[1] = R[1][0] * vec[0] + R[1][1] * vec[1];
    return result;
};

template std::vector<double> rotate_2d_vector<int>(std::vector<int> &vec, const double &theta);
template std::vector<double> rotate_2d_vector<double>(std::vector<double> &vec, const double &theta);

// Returns distance |Am - RBn|
template <typename T>
double get_distance(std::vector<T> &Am, std::vector<T> &RBn)
{
    double norm;
    norm = (Am[0] - RBn[0]) * (Am[0] - RBn[0]);
    norm += (Am[1] - RBn[1]) * (Am[1] - RBn[1]);
    norm = sqrt(norm);
    return norm;
};

template double get_distance<int>(std::vector<int> &Am, std::vector<int> &RBn);
template double get_distance<double>(std::vector<double> &Am, std::vector<double> &RBn);

// Function to return gcd of a and b
int get_gcd(int a, int b)
{
    if (a == 0)
        return b;
    return get_gcd(b % a, a);
}

// Function to find gcd of array of numbers
int find_gcd(std::vector<int> &arr, int n)
{
    int result = arr[0];
    for (int i = 1; i < n; i++)
    {
        result = get_gcd(arr[i], result);

        if (result == 1)
        {
            return 1;
        }
    }
    return result;
}

// Function to perform dot product of row vector(3) times matrix(3,3)
template <typename T>
std::vector<T> vec1x3_dot_3x3_matrix(std::vector<T> &a, std::vector<std::vector<T>> &matrix)
{
    std::vector<T> b(3, 0);
    for (int i = 0; i < a.size(); i++)
    {
        b[i] = a[0] * matrix[0][i] + a[1] * matrix[1][i] + a[2] * matrix[2][i];
    }
    return b;
};

template std::vector<int> vec1x3_dot_3x3_matrix<int>(std::vector<int> &a, std::vector<std::vector<int>> &matrix);
template std::vector<double> vec1x3_dot_3x3_matrix<double>(std::vector<double> &a, std::vector<std::vector<double>> &matrix);

// Function to get determinant of 3x3 matrix
template <typename T>
double get_3x3_matrix_determinant(std::vector<std::vector<T>> &mat)
{
    double determinant = 0;

    //finding determinant
    for (int i = 0; i < 3; i++)
        determinant = determinant + (mat[0][i] * (mat[1][(i + 1) % 3] * mat[2][(i + 2) % 3] - mat[1][(i + 2) % 3] * mat[2][(i + 1) % 3]));

    return determinant;
};

template double get_3x3_matrix_determinant<int>(std::vector<std::vector<int>> &mat);
template double get_3x3_matrix_determinant<double>(std::vector<std::vector<double>> &mat);

// Function to get inverse of 3x3 matrix
template <typename T>
std::vector<std::vector<double>> invert_3x3_matrix(std::vector<std::vector<T>> &mat)
{
    double determinant = get_3x3_matrix_determinant(mat);
    std::vector<std::vector<double>> minv(3, std::vector<double>(3, 0)); // inverse of matrix m
    for (int i = 0; i < 3; i++)
    {
        for (int j = 0; j < 3; j++)
            minv[i][j] = ((mat[(j + 1) % 3][(i + 1) % 3] * mat[(j + 2) % 3][(i + 2) % 3]) - (mat[(j + 1) % 3][(i + 2) % 3] * mat[(j + 2) % 3][(i + 1) % 3])) / determinant;
    }
    return minv;
}

template std::vector<std::vector<double>> invert_3x3_matrix<int>(std::vector<std::vector<int>> &mat);
template std::vector<std::vector<double>> invert_3x3_matrix<double>(std::vector<std::vector<double>> &mat);