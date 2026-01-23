# Hash Benchmarks

This project runs hash tests on various CPU's using the OpenSSL cryptographic
library. [Previous tests](https://github.com/lelegard/cryptobench) have
demonstrated that OpenSSL is usually the fastest cryptographic library, due
to better specialized assembly code in critical operations.

The test algorithms are SHA1, SHA2 and SHA3. With SHA2 and SHA3, the only
tested digest sizes are 256 and 512 bits.

Note: this project is part of a series of cryptographic benchmarks:
- [aesbench](https://github.com/lelegard/aesbench) for AES
- [shabench](https://github.com/lelegard/shabench) for SHA-x hash functions
- [rsabench](https://github.com/lelegard/rsabench) for RSA
- [eccbench](https://github.com/lelegard/rsabench) for ECC (signature only)
- [pqcbench](https://github.com/lelegard/pqcbench) for PQC (ML-KEM, ML-DSA, SLH-DSA)

## Performance results

The performances are evaluated on repeated hash operations on the same 64 kB data.

The results are summarized in file [RESULTS.txt](RESULTS.txt).
It is generated using the Python script `analyze-results.py`.

Two tables are provided:

- Hash bitrates (how many bits are hashed per second when the CPU core runs at
  full speed for that operation).

- Hashed bits per CPU cycle. This metrics is independent of the CPU frequency
  and demonstrates the quality of implementation as well as the number of
  pipelines which are able to process specialized hash instructions.

In each table, the ranking of each CPU in the line is added between brackets.

## Hardware acceleration

Most CPU cores have specialized SHA instructions which speeds up the hash
operations. In the Arm architecture, the SHA instructions belong to the "Neon"
SIMD instruction set.

For export reasons, the Arm Cortex A53 and A72 in Raspberry Pi 3 and 4 have no
specialized SHA instructions. The SHA algorithms are implemented with a portable
C code which is much slower. All other cores in these tests, Intel or Arm, have
SHA instructions.
