/* SPDX-License-Identifier: MIT */
/* Hardware-only GLES rendering and pixel readback, with periodic idle gaps. */
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES2/gl2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double now(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}

static GLuint shader(GLenum type, const char *source)
{
    GLuint id = glCreateShader(type);
    GLint ok = 0;
    glShaderSource(id, 1, &source, NULL);
    glCompileShader(id);
    glGetShaderiv(id, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        char log[4096];
        glGetShaderInfoLog(id, sizeof(log), NULL, log);
        fprintf(stderr, "SHADER_FAILED %s\n", log);
        exit(4);
    }
    return id;
}

int main(int argc, char **argv)
{
    int seconds = argc == 2 ? atoi(argv[1]) : 1;
    if (argc > 2 || seconds < 1 || seconds > 240)
        return 2;
    EGLDisplay dpy = eglGetPlatformDisplay(EGL_PLATFORM_SURFACELESS_MESA, EGL_DEFAULT_DISPLAY, NULL);
    EGLint major, minor, count;
    EGLConfig config;
    const EGLint attrs[] = {EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT, EGL_RED_SIZE, 8,
        EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8, EGL_NONE};
    const EGLint surface_attrs[] = {EGL_WIDTH, 64, EGL_HEIGHT, 64, EGL_NONE};
    const EGLint ctx_attrs[] = {EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE};
    if (!eglInitialize(dpy, &major, &minor) || !eglBindAPI(EGL_OPENGL_ES_API) ||
        !eglChooseConfig(dpy, attrs, &config, 1, &count) || count != 1) {
        fprintf(stderr, "EGL_INIT_FAILED 0x%x\n", eglGetError());
        return 2;
    }
    EGLSurface surface = eglCreatePbufferSurface(dpy, config, surface_attrs);
    EGLContext context = eglCreateContext(dpy, config, EGL_NO_CONTEXT, ctx_attrs);
    if (!eglMakeCurrent(dpy, surface, surface, context))
        return 2;
    const char *renderer = (const char *) glGetString(GL_RENDERER);
    const char *vendor = (const char *) glGetString(GL_VENDOR);
    printf("GL_VENDOR=%s\nGL_RENDERER=%s\nGL_VERSION=%s\n",
           vendor ? vendor : "NULL", renderer ? renderer : "NULL", glGetString(GL_VERSION));
    fflush(stdout);
    if (!renderer || !strstr(renderer, "Adreno") || !strstr(renderer, "830") ||
        !vendor || !strstr(vendor, "freedreno")) {
        fprintf(stderr, "HARDWARE_REQUIRED: refusing software/other GPU result\n");
        return 3;
    }
    GLuint vs = shader(GL_VERTEX_SHADER,
        "attribute vec2 p; void main(){gl_Position=vec4(p,0.,1.);}");
    GLuint fs = shader(GL_FRAGMENT_SHADER,
        "precision mediump float; uniform float phase; void main(){"
        "float r=step(32.,gl_FragCoord.x); float g=step(32.,gl_FragCoord.y);"
        "gl_FragColor=vec4(r,g,phase,1.);}");
    GLuint prog = glCreateProgram();
    glAttachShader(prog, vs);
    glAttachShader(prog, fs);
    glBindAttribLocation(prog, 0, "p");
    glLinkProgram(prog);
    GLint linked;
    glGetProgramiv(prog, GL_LINK_STATUS, &linked);
    if (!linked)
        return 4;
    glUseProgram(prog);
    const GLfloat points[] = {-1.f, -1.f, 3.f, -1.f, -1.f, 3.f};
    GLuint vbo;
    glGenBuffers(1, &vbo);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(points), points, GL_STATIC_DRAW);
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, NULL);
    glEnableVertexAttribArray(0);
    glViewport(0, 0, 64, 64);
    GLint phase = glGetUniformLocation(prog, "phase");
    unsigned char pixels[64 * 64 * 4];
    unsigned frames = 0, idle_gaps = 0;
    double start = now();
    do {
        unsigned blue = (frames & 1) ? 255 : 0;
        glClearColor(0.5f, 0.5f, 0.5f, 0.5f);
        glClear(GL_COLOR_BUFFER_BIT);
        glUniform1f(phase, blue / 255.f);
        glDrawArrays(GL_TRIANGLES, 0, 3);
        glReadPixels(0, 0, 64, 64, GL_RGBA, GL_UNSIGNED_BYTE, pixels);
        if (glGetError() != GL_NO_ERROR)
            return 5;
        for (int y = 0; y < 64; y++) {
            for (int x = 0; x < 64; x++) {
                const unsigned char *p = &pixels[(y * 64 + x) * 4];
                if (p[0] != (x >= 32 ? 255 : 0) || p[1] != (y >= 32 ? 255 : 0) ||
                    p[2] != blue || p[3] != 255) {
                    fprintf(stderr, "PIXEL_FAILED frame=%u x=%d y=%d rgba=%u,%u,%u,%u\n",
                            frames, x, y, p[0], p[1], p[2], p[3]);
                    return 6;
                }
            }
        }
        frames++;
        struct timespec delay = {0, 8000000};
        if (!(frames % 100)) {
            delay.tv_nsec = 700000000;
            idle_gaps++;
        }
        nanosleep(&delay, NULL);
    } while (now() - start < seconds);
    printf("GPU_PIXELS_PASS frames=%u idle_gaps=%u elapsed=%.3f\n", frames, idle_gaps, now() - start);
    glDeleteBuffers(1, &vbo);
    glDeleteProgram(prog);
    glDeleteShader(vs);
    glDeleteShader(fs);
    eglMakeCurrent(dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    eglDestroyContext(dpy, context);
    eglDestroySurface(dpy, surface);
    eglTerminate(dpy);
    return 0;
}
