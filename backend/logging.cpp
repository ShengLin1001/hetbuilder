#include <vector>
#include <iostream>

#ifdef _OPENMP
#include <omp.h>
#endif

using std::vector;

template <typename T>
void print_2d_vector(const vector<vector<T>> &vec)
{
    for (vector<vector<float>>::size_type i = 0; i < vec.size(); i++)
    {
        for (vector<float>::size_type j = 0; j < vec[i].size(); j++)
        {
            std::cout << vec[i][j] << ' ';
        }
        std::cout << std::endl;
    }
}

void log_number_of_threads()
{
    int limit, maxthreads;
    limit = omp_get_thread_limit();
    maxthreads = omp_get_max_threads();
    printf("Limit is %d.\n", limit);
    printf("Max is %d.\n", maxthreads);

#pragma omp parallel
    printf("Hello from thread %d of %d .\n", omp_get_thread_num(), omp_get_num_threads());
};