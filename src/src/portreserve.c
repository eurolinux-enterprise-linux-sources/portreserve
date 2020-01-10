/*
 * portreserve - reserve ports to prevent portmap mapping them
 * portrelease - allow the real service to bind to its port
 * Copyright (C) 2003, 2008 Tim Waugh <twaugh@redhat.com>
 *
 * This program contains daemon_lock_pidfile and fcntl_lock taken
 * from libslack.  Libslack is Copyright (C) 1999-2004 raf <raf@raf.org>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 */

#include "config.h"

#if HAVE_DIRENT_H
# include <dirent.h>
#endif

#include <errno.h>
#include <error.h>

#if HAVE_NETDB_H
# include <netdb.h>
#endif

#if HAVE_NETINET_IN_H
# include <netinet/in.h>
#endif

#if HAVE_STDLIB_H
# include <stdlib.h>
#endif

#include <stdio.h>

#if HAVE_STRING_H
# include <string.h>
#endif

#if HAVE_SYS_SELECT_H
# include <sys/select.h>
#endif

#if HAVE_SYS_SOCKET_H
# include <sys/socket.h>
#endif

#if HAVE_SYS_TYPES_H
# include <sys/types.h>
#endif

#include <sys/un.h>

#if HAVE_UNISTD_H
# include <unistd.h>
#endif

#include <signal.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#define UNIX_SOCKET "/var/run/portreserve/socket"
#define PIDFILE "/var/run/portreserve.pid"

struct map {
	struct map *next;
	char *service;
	int socket;
};

static int debug = 0;

static int
portrelease (const char *service)
{
	struct sockaddr_un addr;
	int s = socket (PF_UNIX, SOCK_DGRAM, 0);
	if (s == -1)
		return -1;
	addr.sun_family = AF_UNIX;
	strcpy (addr.sun_path, UNIX_SOCKET);
	if (connect (s, (struct sockaddr *) &addr, sizeof (addr)) == -1)
		/* portreserve not running; nothing to do. */
		return 0;
	send (s, service, strlen (service), 0);
	close (s);
	return 0;
}

static int
real_file (const char *name)
{
	if (strchr (name, '~'))
		return 0;
	if (strchr (name, '.'))
		return 0;
	return 1;
}

static void
no_memory (void)
{
	exit (1);
}

static struct map *
reserve (const char *file, const char *client)
{
	struct map *maps = NULL;
	FILE *f = fopen (file, "r");
	if (!f)
		return NULL;

	for (;;) {
		char service[100];
		char *protocols[2] = { "tcp", "udp" };
		size_t num_protocols = 2;
		size_t i;

		char *p = fgets (service, sizeof (service), f);
		if (!p) {
			fclose (f);
			return maps;
		}

		p += strcspn (service, "/\n");
		if (*p == '/') {
			*p = '\0';
			protocols[0] = p + 1;
			p = strchr (protocols[0], '\n');
			num_protocols = 1;
		}

		if (p)
			*p = '\0';

		for (i = 0; i < num_protocols; i++) {
			struct map *map;
			struct sockaddr_in sin;
			int sd;
			int type;
			const char *protocol = protocols[i];
			struct servent *serv = getservbyname (service,
							      protocol);
			if (serv)
				sin.sin_port = (in_port_t) serv->s_port;
			else {
				char *endptr;
				int port = strtol (service, &endptr, 10);
				if (service == endptr)
					/* Not found for this protocol. */
					continue;

				/* Numeric entry */
				sin.sin_port = htons (port);
			}

			sin.sin_family = AF_INET;
			sin.sin_addr.s_addr = INADDR_ANY;

			if (!strcmp (protocol, "udp"))
				type = SOCK_DGRAM;
			else
				type = SOCK_STREAM;

			sd = socket (PF_INET, type, 0);
			if (sd == -1) {
				if (debug)
					fprintf (stderr,
						 "Unable to create %s socket\n",
						 protocol);
				continue;
			}

			if (bind (sd, (struct sockaddr *) &sin,
				  sizeof (sin)) == -1) {
				error (0, errno, "bind");
				continue;
			}

			map = malloc (sizeof (*map));
			if (!map)
				no_memory ();
			map->socket = sd;
			map->next = maps;
			map->service = strdup (client);
			if (!map->service)
				no_memory ();
			maps = map;

			if (debug)
				fprintf (stderr, "Reserved %d/%s for %s\n",
					 ntohs (sin.sin_port),
					 protocol, client);
		}
	}

	return maps;
}

static int
unix_socket (void)
{
	struct sockaddr_un addr;
	int s = socket (PF_UNIX, SOCK_DGRAM, 0);
	if (s == -1)
		return s;
	addr.sun_family = AF_UNIX;
	strcpy (addr.sun_path, UNIX_SOCKET);
	if (bind (s, (struct sockaddr *) &addr, sizeof (addr)) == -1) {
		if (connect (s, (struct sockaddr *) &addr,
			     sizeof (addr)) == 0) {
			close (s);
			error (EXIT_FAILURE, 0, "already running");
		}
		unlink (UNIX_SOCKET);
		if (bind (s, (struct sockaddr *) &addr,
			  sizeof (addr)) == -1) {
			close (s);
			error (EXIT_FAILURE, errno, "bind");
		}
	}
	return s;
}

static int
portreserve (void)
{
	struct map *maps = NULL;
	const char *dir = "/etc/portreserve/";
	char *cfgfile = malloc (strlen (dir) + NAME_MAX + 1);
	char *cfgf = cfgfile + strlen (dir);
	struct dirent *d;
	int unfd = unix_socket ();
	DIR *cfgdir;
	if (!cfgfile)
		return -1;
	strcpy (cfgfile, dir);
	cfgdir = opendir (dir);
	if (!cfgdir)
		return -1;
	while ((d = readdir (cfgdir)) != NULL) {
		struct map *newmaps, *p;
		int s;
		if (!real_file (d->d_name))
			continue;
		strcpy (cfgf, d->d_name);
		if ((newmaps = reserve (cfgfile, d->d_name)) == NULL)
			continue;

		for (p = newmaps; p && p->next != NULL; p = newmaps->next)
			;
		if (p)
			p->next = maps;

		if (newmaps)
			maps = newmaps;
	}
	closedir (cfgdir);

	while (maps) {
		fd_set fds;
		FD_ZERO (&fds);
		FD_SET (unfd, &fds);
		if (select (unfd + 1, &fds, NULL, NULL, NULL) &&
		    FD_ISSET (unfd, &fds)) {
			char service[100];
			ssize_t got;
			struct map *m, **prev;
			got = recv (unfd, service, sizeof (service) - 1, 0);
			if (got == -1)
				continue;
			service[got] = '\0';
			prev = &maps;
			m = maps;
			while (m) {
				if (!strcmp (service, "*") ||
				    !strcmp (m->service, service)) {
					struct map *next = m->next;

					if (debug)
						fprintf (stderr,
							 "Released service "
							 "%s\n", m->service);
					close (m->socket);
					free (m->service);
					free (m);
					m = next;
					maps = NULL;
				} else {
					prev = &m->next;
					m = *prev;
				}
			}
		}
	}

	if (debug)
		fprintf (stderr, "All reservations taken.\n");

	return 0;
}

/* daemon_lock_pidfile and fcntl_lock taken from libslack 
 * Copyright (C) 1999-2004 raf <raf@raf.org>
 * Licensed under the GPL
 */
int 
fcntl_lock(int fd, int cmd, int type, int whence, int start, int len)
{
        struct flock lock[1];

        lock->l_type = type;
        lock->l_whence = whence;
        lock->l_start = start;
        lock->l_len = len;

        return fcntl(fd, cmd, lock);
}

static int 
daemon_lock_pidfile(char *pidfile)
{
        mode_t mode = S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH;
        int pid_fd;

        /* This is broken over NFS (Linux). So pidfiles must reside locally. */

        if ((pid_fd = open(pidfile, O_RDWR | O_CREAT | O_EXCL, mode)) == -1)
        {
                if (errno != EEXIST)
                        return -1;

                /*
                ** The pidfile already exists. Is it locked?
                ** If so, another invocation is still alive.
                ** If not, the invocation that created it has died.
                ** Open the pidfile to attempt a lock.
                */

                if ((pid_fd = open(pidfile, O_RDWR)) == -1)
                        return -1;
        }

        if (fcntl_lock(pid_fd, F_SETLK, F_WRLCK, SEEK_SET, 0, 0) == -1)
                return -1;

        return pid_fd;
}

int 
create_pidfile(char *pidfile)
{

	int fd;
	char pid[32];
	
	/* Open and lock pidfile */
	if ((fd = daemon_lock_pidfile(pidfile)) == -1) {
		return -1;
	}

	/* Store our pid */
	snprintf(pid, sizeof(pid), "%d\n", (int)getpid());
	if (write(fd, pid, strlen(pid)) != strlen(pid)) {
		return -1;
	}

	return 0;
}

void
handle_signal (int sig)
{
	printf("Cleaning pidfile\n");
	unlink(PIDFILE);
	exit(0);
}

int
main (int argc, char **argv)
{
	int rv;
	const char *p = strrchr (argv[0], '/');
	if (!p++)
		p = argv[0];

	if (strstr (p, "portrelease")) {
		int i;
		int r = 0;
		for (i = 1; i < argc; i++)
			r += portrelease (argv[i]);
		return r;
	}
	
	signal (SIGTERM, handle_signal);
	signal (SIGINT, handle_signal);
	signal (SIGQUIT, handle_signal);
	signal (SIGKILL, handle_signal);
	
	if (argc > 1) {
		if (!strcmp (argv[1], "-d"))
			debug = 1;
		else
			error (EXIT_FAILURE, 0,
			       "See the man page to find out "
			       "what this program does.");
	}

	if (!debug) {
		switch (fork ()) {
		case 0:
			break;
		case -1:
			error (EXIT_FAILURE, errno, "fork");
		default:
			return 0;
		}

		close (STDIN_FILENO);
		close (STDOUT_FILENO);
		close (STDERR_FILENO);
		setsid ();
	}
	if (create_pidfile(PIDFILE)==-1)
		error (EXIT_FAILURE, errno, 
				"Failed to write pidfile!");

	rv = portreserve();
	unlink(PIDFILE);
	return rv;
}
