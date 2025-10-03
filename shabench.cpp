//----------------------------------------------------------------------------
// shabench - Copyright (c) 2025, Thierry Lelegard
// BSD 2-Clause License, see LICENSE file.
//----------------------------------------------------------------------------

#include <iostream>
#include <vector>
#include <cstdlib>
#include <cinttypes>

#include <openssl/opensslv.h>
#include <openssl/evp.h>
#include <openssl/err.h>

#if defined(WINDOWS)
    #include <Windows.h>
#else
    #include <sys/resource.h>
#endif

constexpr int64_t USECPERSEC = 1000000;  // microseconds per second
constexpr int64_t MIN_CPU_TIME = 2 * USECPERSEC;
constexpr size_t  DATA_SIZE = 64 * 1024 * 1024;
constexpr size_t  INNER_LOOP_COUNT = 10;


//----------------------------------------------------------------------------
// Get current CPU time resource usage in microseconds.
//----------------------------------------------------------------------------

int64_t cpu_time()
{
    rusage ru;
    if (getrusage(RUSAGE_SELF, &ru) < 0) {
        perror("getrusage");
        exit(EXIT_FAILURE);
    }
    return ((int64_t)(ru.ru_utime.tv_sec) * USECPERSEC) + ru.ru_utime.tv_usec +
           ((int64_t)(ru.ru_stime.tv_sec) * USECPERSEC) + ru.ru_stime.tv_usec;
}


//----------------------------------------------------------------------------
// OpenSSL error, abort application.
//----------------------------------------------------------------------------

[[noreturn]] void fatal(const std::string& message)
{
    if (!message.empty()) {
        std::cerr << "openssl: " << message << std::endl;
    }
    ERR_print_errors_fp(stderr);
    std::exit(EXIT_FAILURE);
}


//----------------------------------------------------------------------------
// Perform one test
//----------------------------------------------------------------------------

void one_test(const EVP_MD* evp)
{
    const size_t digest_size = EVP_MD_get_size(evp);
    std::vector<uint8_t> input(DATA_SIZE);
    std::vector<uint8_t> output(digest_size);

    // Generate input data with all different bytes.
    uint8_t byte = 0x23;
    for (auto& b : input) {
        b = byte++;
    }

    std::cout << "algo: " << EVP_MD_get0_name(evp) << std::endl;
    std::cout << "digest-size: " << digest_size << std::endl;
    std::cout << "data-size: " << input.size() << std::endl;

    // Initialize hash context.
    EVP_MD_CTX* ctx = EVP_MD_CTX_new();
    if (ctx == nullptr) {
        fatal("error creating hash context");
    }

    uint64_t size = 0;
    uint64_t duration = 0;
    uint64_t start = cpu_time();
    do {
        for (size_t i = 0; i < INNER_LOOP_COUNT; i++) {
            if (EVP_Digest(input.data(), input.size(), output.data(), nullptr, evp, nullptr) == 0) {
                fatal("digest error");
            }
            size += input.size();
        }
        duration = cpu_time() - start;
    } while (duration < MIN_CPU_TIME);

    EVP_MD_CTX_free(ctx);

    std::cout << "hash-microsec: " << duration << std::endl;
    std::cout << "hash-size: " << size << std::endl;
    std::cout << "hash-bitrate: " << ((USECPERSEC * 8 * size) / duration) << std::endl;
}


//----------------------------------------------------------------------------
// Application entry point
//----------------------------------------------------------------------------

int main(int argc, char* argv[])
{
    // OpenSSL initialization.
    ERR_load_crypto_strings();
    OpenSSL_add_all_algorithms();
    std::cout << "openssl: "
#if defined(OPENSSL_FULL_VERSION_STRING) // v3
              << OpenSSL_version(OPENSSL_FULL_VERSION_STRING) << ", " << OpenSSL_version(OPENSSL_CPU_INFO)
#elif defined(OPENSSL_VERSION)
              << OpenSSL_version(OPENSSL_VERSION)
#else
              << OPENSSL_VERSION_TEXT
#endif
              << std::endl;

    // Run tests.
    one_test(EVP_sha1());
    one_test(EVP_sha256());
    one_test(EVP_sha512());
    one_test(EVP_sha3_256());
    one_test(EVP_sha3_512());

    // OpenSSL cleanup.
    EVP_cleanup();
    ERR_free_strings();
    return EXIT_SUCCESS;
}
